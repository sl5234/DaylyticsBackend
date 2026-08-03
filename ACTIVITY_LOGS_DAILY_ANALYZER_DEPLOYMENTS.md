# Activity Logs Daily Analyzer - AWS Deployment Log

Tracks AWS resources created for running `scripts/run_daily_workflow.py` on a
schedule via Lambda + EventBridge, and the exact commands used to create
them. Account: `792341830430`, region: `us-west-2` throughout.

The `file://iam_policies/*.json` paths referenced below aren't checked into
the repo - the roles are already created in AWS, so the JSON blocks shown
inline above each command are kept here only as the record of what was
applied. To recreate a role, save the relevant JSON block to that path
first.

## 1. S3 bucket (output CSV storage)

Bucket: `activitylogs-daily-analysis-outputs-792341830430-us-west-2`

```bash
aws s3api create-bucket \
  --bucket activitylogs-daily-analysis-outputs-792341830430-us-west-2 \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2
```

Public access block left at the account default (all four settings `true` -
`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`,
`RestrictPublicBuckets`); verified with:

```bash
aws s3api get-public-access-block \
  --bucket activitylogs-daily-analysis-outputs-792341830430-us-west-2
```

## 2. IAM execution role

Role: `ActivityLogsDailyAnalyzerExecutionRole`
ARN: `arn:aws:iam::792341830430:role/ActivityLogsDailyAnalyzerExecutionRole`

Trust policy (`lambda.amazonaws.com` may assume this role):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

```bash
aws iam create-role \
  --role-name ActivityLogsDailyAnalyzerExecutionRole \
  --assume-role-policy-document file://iam_policies/lambda-trust-policy.json \
  --description "Execution role for the Daylytics daily activity log analysis Lambda"
```

Inline permissions policy (`ActivityLogsDailyAnalyzerPermissions`) - scoped to
exactly the resources this job touches, no wildcards:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": "arn:aws:kms:us-west-2:792341830430:key/f46115bb-774a-4777-ab66-29903da24381"
    },
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-west-2:792341830430:DaylyticsDailyActivityLogsAnalysis"
    },
    {
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::activitylogs-daily-analysis-outputs-792341830430-us-west-2/*"
    }
  ]
}
```

```bash
aws iam put-role-policy \
  --role-name ActivityLogsDailyAnalyzerExecutionRole \
  --policy-name ActivityLogsDailyAnalyzerPermissions \
  --policy-document file://iam_policies/lambda-permissions-policy.json

aws iam attach-role-policy \
  --role-name ActivityLogsDailyAnalyzerExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

The `kms:Decrypt` grant above works without editing the KMS key's own
resource policy: the key policy has an `"Enable IAM User Permissions"`
statement granting the account root full `kms:*`, which delegates
authorization to IAM - any role in the account with an IAM policy allowing
`kms:Decrypt` on this key can use it.

Pre-existing, unrelated Lambda functions were found in this account
(market-analysis/execution-plan project) - left untouched, not part of this
work.

## 3. Lambda deployment package

Built via `scripts/build_lambda_package.sh`:

```bash
bash scripts/build_lambda_package.sh
```

- Installs `requirements-lambda.txt` (a lean subset of `requirements.txt` -
  excludes `uvicorn`, `pdfplumber`, `pytest`/`black`/`ruff`/`mypy`; `boto3`
  was intentionally left out too since the Lambda Python runtime provides it
  natively, but it ends up bundled anyway as a transitive dependency of
  `appdevcommons` - harmless, just extra size).
- Preserves the repo's `scripts/` + `app/` layout inside the zip (rather than
  flattening it) so `run_daily_workflow.py`'s existing
  `REPO_ROOT = Path(__file__).resolve().parent.parent` path logic resolves
  correctly in both local and Lambda contexts without modification.
- Also copies `personal_prompt_temporary.py` (gitignored/personal, required
  at runtime by `app/routes/workflow.py`).
- Output: `build/daily_workflow_lambda.zip` (~21 MB, well under the 50 MB
  zipped / 250 MB unzipped Lambda limits - no container image needed).
- Lambda handler value: `scripts.run_daily_workflow.lambda_handler`

## 4. Lambda function

Function: `ActivityLogsDailyAnalyzerFunction`
ARN: `arn:aws:lambda:us-west-2:792341830430:function:ActivityLogsDailyAnalyzerFunction`

```bash
aws lambda create-function \
  --function-name ActivityLogsDailyAnalyzerFunction \
  --runtime python3.13 \
  --role arn:aws:iam::792341830430:role/ActivityLogsDailyAnalyzerExecutionRole \
  --handler scripts.run_daily_workflow.lambda_handler \
  --zip-file fileb:///Users/sl5234/Workspace/DaylyticsBackend/build/daily_workflow_lambda.zip \
  --timeout 300 \
  --memory-size 512 \
  --region us-west-2 \
  --description "Runs the Daylytics daily activity log analysis workflow on a schedule"
```

- Timeout 300s (5 min) - default 3s is nowhere near enough for the Toggl +
  OpenAI API calls this makes.
- Memory 512MB - default 128MB was judged too tight given the import graph
  (openai, httpx, pydantic) plus the analysis ThreadPoolExecutor.
- No environment variables set - `Settings` (`app/config.py`) reads all
  config from hardcoded field defaults (the encrypted Toggl/OpenAI
  credentials, KMS key ARN, SNS topic ARN, S3 bucket); `SettingsConfigDict(env_file=".env")`
  tolerates the `.env` file not existing in the Lambda package.

To redeploy after a code change:

```bash
bash scripts/build_lambda_package.sh
aws lambda update-function-code \
  --function-name ActivityLogsDailyAnalyzerFunction \
  --zip-file fileb:///Users/sl5234/Workspace/DaylyticsBackend/build/daily_workflow_lambda.zip \
  --region us-west-2
```

## 5. EventBridge schedule

Schedule: `ActivityLogsDailyAnalyzerSchedule`
ARN: `arn:aws:scheduler:us-west-2:792341830430:schedule/default/ActivityLogsDailyAnalyzerSchedule`

Uses EventBridge **Scheduler** (not the older EventBridge Rules), because it
supports an explicit IANA timezone (`America/Los_Angeles`) - classic
`events put-rule` cron expressions are UTC-only, which would have drifted an
hour relative to Pacific time across DST transitions.

IAM role (`ActivityLogsDailyAnalyzerSchedulerRole`) letting EventBridge
Scheduler invoke the Lambda:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "scheduler.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-west-2:792341830430:function:ActivityLogsDailyAnalyzerFunction"
    }
  ]
}
```

```bash
aws iam create-role \
  --role-name ActivityLogsDailyAnalyzerSchedulerRole \
  --assume-role-policy-document file://iam_policies/scheduler-trust-policy.json \
  --description "Allows EventBridge Scheduler to invoke the Daylytics daily analyzer Lambda"

aws iam put-role-policy \
  --role-name ActivityLogsDailyAnalyzerSchedulerRole \
  --policy-name ActivityLogsDailyAnalyzerSchedulerInvokePermission \
  --policy-document file://iam_policies/scheduler-permissions-policy.json
```

Schedule itself - daily at 9:00 PM Pacific, no payload (so it uses
`lambda_handler`'s default target day, yesterday). Originally created at
11:59 PM and moved earlier via `aws scheduler update-schedule` with the same
parameters below:

```bash
aws scheduler create-schedule \
  --name ActivityLogsDailyAnalyzerSchedule \
  --schedule-expression "cron(0 21 * * ? *)" \
  --schedule-expression-timezone "America/Los_Angeles" \
  --flexible-time-window '{"Mode": "OFF"}' \
  --target '{
    "Arn": "arn:aws:lambda:us-west-2:792341830430:function:ActivityLogsDailyAnalyzerFunction",
    "RoleArn": "arn:aws:iam::792341830430:role/ActivityLogsDailyAnalyzerSchedulerRole",
    "Input": "{}"
  }' \
  --state ENABLED \
  --region us-west-2
```

To pause/resume without deleting it:

```bash
aws scheduler update-schedule --name ActivityLogsDailyAnalyzerSchedule --region us-west-2 --state DISABLED ...  # (full schedule config must be repeated)
```

## Troubleshooting notes from deployment testing

A few real issues hit while getting the first successful invocation, in case
they recur after a dependency bump or a fresh package build:

- **`No module named 'pydantic_core._pydantic_core'`**: building the zip with
  plain `pip install -t` on macOS grabs the macOS-compiled binary for
  packages with native extensions (`pydantic_core`). Lambda runs on Linux, so
  that binary fails to import. Fixed by forcing
  `--platform manylinux2014_x86_64 --implementation cp --python-version 3.13
  --only-binary=:all:` in `scripts/build_lambda_package.sh`, regardless of
  the host OS building the package.
- **`No module named 'pdfplumber'`**: `app/routes/workflow.py` imported
  `get_toggl_track_activity_logs_from_pdf` unconditionally at module level,
  even though this Lambda only ever uses `TOGGL_API` mode. Rather than
  bundling `pdfplumber` (which pulls in Pillow and pypdfium2 - another
  package with platform-specific compiled binaries, reintroducing the same
  risk), made the import lazy: it now only happens inside the
  `if mode == TOGGL_PDF` branch that actually needs it.
- **Missing `INFO`-level logs in CloudWatch**: Lambda's runtime pre-attaches
  its own root logging handler before application code runs, which makes
  `logging.basicConfig()` a no-op unless called with `force=True`. Without
  it, only `WARNING`+ messages showed up even though `level=logging.INFO`
  was passed.

Verified working: first successful invocation wrote
`AnalysisOutput2026-08-012026-08-01.csv` to the S3 bucket and published one
message to the SNS topic (confirmed via the `AWS/SNS NumberOfMessagesPublished`
CloudWatch metric and receipt of the actual email).
