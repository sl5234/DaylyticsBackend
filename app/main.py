from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from app.config import settings
from app.routes import analysis, plan, workflow
from app.dagger.aws_clients import AWSClients

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def _initialize_aws_clients(app: FastAPI) -> None:
    """
    Initialize AWS clients and store them in app state and config.

    AWS credentials are resolved from environment variables, IAM roles, or credential files.

    Args:
        app: FastAPI application instance

    Raises:
        Exception: If AWS client initialization fails
    """
    aws_clients = AWSClients(
        region_name=None
    )  # Uses default region from env or boto3 config
    aws_clients.initialize()
    app.state.aws_clients = aws_clients
    settings.set_aws_clients(aws_clients)
    logger.info("AWS clients initialized and stored in app state and config")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.

    Initializes AWS clients at startup and stores them in app state.
    AWS credentials are resolved from environment variables, IAM roles, or credential files.
    """
    logger.info("Starting up application...")
    try:
        _initialize_aws_clients(app)
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")
        # Decide whether to fail fast or continue without AWS
        # For now, we'll raise to fail fast
        raise

    yield

    # Shutdown: Cleanup if needed
    logger.info("Shutting down application...")
    # AWS clients don't need explicit cleanup, but we can log
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name, debug=settings.debug, version="1.0.0", lifespan=lifespan
)

# Include routers
app.include_router(plan.router)
app.include_router(analysis.router)
app.include_router(workflow.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Daylytics Backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
