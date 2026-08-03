#!/usr/bin/env bash
# Builds the zip deployment package for the daily workflow Lambda.
#
# Preserves the repo's scripts/ + app/ layout inside the package (rather
# than flattening it) so run_daily_workflow.py's existing
# REPO_ROOT = Path(__file__).resolve().parent.parent path logic resolves
# correctly in both contexts without special-casing. Lambda handler value:
# scripts.run_daily_workflow.lambda_handler
#
# Usage: scripts/build_lambda_package.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/build/lambda_package"
ZIP_PATH="$REPO_ROOT/build/daily_workflow_lambda.zip"

echo "Cleaning previous build..."
rm -rf "$BUILD_DIR" "$ZIP_PATH"
mkdir -p "$BUILD_DIR/scripts"

echo "Installing Lambda dependencies (requirements-lambda.txt)..."
# Force Linux/x86_64 wheels regardless of the host OS - packages with
# compiled extensions (e.g. pydantic_core) otherwise install the local
# platform's binary, which fails to import on Lambda's Linux runtime.
# Must match the Lambda function's configured runtime/architecture.
pip install \
  -r "$REPO_ROOT/requirements-lambda.txt" \
  -t "$BUILD_DIR" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.13 \
  --only-binary=:all: \
  --quiet

echo "Copying application code..."
cp -R "$REPO_ROOT/app" "$BUILD_DIR/app"
cp "$REPO_ROOT/scripts/run_daily_workflow.py" "$BUILD_DIR/scripts/run_daily_workflow.py"
cp "$REPO_ROOT/personal_prompt_temporary.py" "$BUILD_DIR/personal_prompt_temporary.py"

echo "Stripping __pycache__..."
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "Zipping..."
(cd "$BUILD_DIR" && zip -r -q "$ZIP_PATH" .)

echo "Built $ZIP_PATH ($(du -h "$ZIP_PATH" | cut -f1))"
