# DaylyticsBackend

A Python backend API built with FastAPI.

## Setup

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
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

## Verification

To confirm the package builds correctly, run these commands:

1. **Verify packages installed correctly:**
   ```bash
   pip list
   # Should show: fastapi, pydantic, pydantic-settings, uvicorn, etc.
   ```

2. **Check Python can import your modules:**
   ```bash
   python -c "from app.main import app; print('✓ Imports successful')"
   ```

3. **Verify FastAPI app loads:**
   ```bash
   python -c "from app.config import settings; print(f'✓ Config loaded: {settings.app_name}')"
   ```

4. **Test the server starts (quick check):**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 &
   sleep 2
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   pkill -f uvicorn
   ```

5. **Or run the server interactively:**
   ```bash
   uvicorn app.main:app --reload
   # Then visit http://localhost:8000/docs in your browser
   # Press Ctrl+C to stop
   ```

**Quick All-in-One Test:**
```bash
# Create venv, install, and test
python3 -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
python -c "from app.main import app; print('✓ Build successful!')" && \
echo "Ready to run: uvicorn app.main:app --reload"
```