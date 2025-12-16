from app.models.metrics import MetricsData
from app.config import settings


def emit_metrics(metrics_data: MetricsData) -> None:
    """
    Emit metrics to the configured backend (CloudWatch or CSV).
    
    Args:
        metrics_data: The metrics data to emit
    """
    if settings.metrics_backend == "cloudwatch":
        emit_to_cloudwatch(metrics_data)
    elif settings.metrics_backend == "csv":
        emit_to_csv(metrics_data)
    else:
        raise ValueError(f"Unknown metrics backend: {settings.metrics_backend}")


def emit_to_cloudwatch(metrics_data: MetricsData) -> None:
    """
    Emit metrics to AWS CloudWatch.
    
    Args:
        metrics_data: The metrics data to emit
    """
    # TODO: Implement CloudWatch emission
    pass


def emit_to_csv(metrics_data: MetricsData) -> None:
    """
    Emit metrics to CSV file.
    
    Args:
        metrics_data: The metrics data to emit
    """
    # TODO: Implement CSV emission
    pass

