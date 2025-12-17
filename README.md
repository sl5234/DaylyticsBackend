# DaylyticsBackend

A Python backend API built with FastAPI.

## How to build and run

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root with the following variables:
   ```bash
   # Application Configuration
   APP_NAME=Daylytics Backend
   DEBUG=False
   DATABASE_URL=sqlite:///./daylytics.db
   
   # Toggl Track API
   TOGGL_API_TOKEN="015c0844c9879a003346041d7b42ea6c"
   TOGGL_EMAIL="smin.lee5234@gmail.com"
   TOGGL_PASSWORD="DLtkdals1!"
   ```

4. **Set up AWS credentials:**
   The application uses AWS services. AWS credentials are resolved using boto3's default credential chain. You can configure credentials using one of the following methods:

   **Option A: Environment variables (recommended for local development):**
   ```bash
   export AWS_ACCESS_KEY_ID="your-access-key-id"
   export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
   export AWS_DEFAULT_REGION="us-east-1"  # Optional: set default region
   ```

   **Option B: AWS credentials file:**
   Create `~/.aws/credentials` with:
   ```ini
   [default]
   aws_access_key_id = your-access-key-id
   aws_secret_access_key = your-secret-access-key
   region = us-east-1
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

## Development Setup

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests:**
   ```bash
   pytest
   ```
   
   Run tests with verbose output:
   ```bash
   pytest -v
   ```
   
   Run a specific test file:
   ```bash
   pytest tests/app/test_config.py
   ```

4. **Verify your code builds and works:**
   The best way to verify your Python library builds and works correctly is to run the test suite:
   ```bash
   pytest
   ```
   
   If all tests pass, your code is working correctly. You can also run the application to verify it starts:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Format code:**
   ```bash
   black app/ tests/
   ```

6. **Lint code:**
   ```bash
   ruff check app/ tests/
   ```

7. **Type checking:**
   ```bash
   mypy app/
   ```