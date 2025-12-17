from typing import Annotated
from fastapi import Depends
from app.dagger.aws_clients import AWSClients


def get_aws_clients(app_state) -> AWSClients:
    """
    FastAPI dependency to get AWS clients from app state.

    This dependency provides access to initialized AWS clients
    throughout the application.

    Args:
        app_state: FastAPI app state containing AWS clients

    Returns:
        AWSClients instance with initialized AWS service clients

    Raises:
        RuntimeError: If AWS clients are not initialized in app state
    """
    if not hasattr(app_state, "aws_clients"):
        raise RuntimeError(
            "AWS clients not found in app state. Ensure they are initialized at startup."
        )
    return app_state.aws_clients


# Type alias for dependency injection
AWSClientsDep = Annotated[AWSClients, Depends(get_aws_clients)]
