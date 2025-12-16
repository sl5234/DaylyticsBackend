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
   TOGGL_API_TOKEN=
   
   # LLM Configuration
   LLM_API_KEY=
   LLM_PROVIDER=openai
   
   # Metrics Configuration
   METRICS_BACKEND=csv
   CLOUDWATCH_REGION=us-east-1
   CLOUDWATCH_NAMESPACE=Daylytics
   CSV_METRICS_PATH=./metrics.csv
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`