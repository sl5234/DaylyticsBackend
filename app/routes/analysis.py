import logging

from fastapi import APIRouter
from appdevcommons.unique_id import UniqueIdGenerator  # type: ignore[import-untyped]
from app.models.analysis import (
    CreateAnalysisRequest,
    AnalysisResponse,
    OutputConfig,
    ResponseMode,
)
from app.agents.analyzers.metric_generator import generate_all_metrics
from app.agents.analyzers.table_generator import generate_table
from app.agents.analyzers.summarizer import generate_summary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/", response_model=AnalysisResponse)
def create_analysis(request: CreateAnalysisRequest) -> AnalysisResponse:  # type: ignore[no-redef]  # noqa: F811  # noqa: F811
    """
    Create analysis for a date range.

    Processes activity logs according to the ResponseMode:
    - METRIC: Generates activity metrics using metric generators
    - TABLE: Generates table representation
    - TEXT: Generates text summary
    """
    logger.info(f"Creating analysis with mode: {request.ResponseMode}")

    # Process based on response mode
    if request.ResponseMode == ResponseMode.METRIC:
        logger.info("Generating metrics from activity logs")
        all_metrics = generate_all_metrics(request.ActivityLogs)
        logger.info(f"Generated {len(all_metrics)} metrics")

    elif request.ResponseMode == ResponseMode.TABLE:
        logger.info("Generating table from activity logs")
        table = generate_table(request.ActivityLogs)
        logger.info(f"Generated table with {len(table)} rows")

    elif request.ResponseMode == ResponseMode.TEXT:
        logger.info("Generating text summary from activity logs")
        summary = generate_summary(request.ActivityLogs)
        logger.info(f"Generated summary with {len(summary)} characters")

    id_generator = UniqueIdGenerator()
    analysis_rid = id_generator.generate_id()

    # Generate S3 output path
    s3_output_path = f"s3://daylytics/analysis/{analysis_rid}/output"

    result = {
        "AnalysisRid": analysis_rid,
        "OutputConfig": {"S3OutputPath": s3_output_path},
    }

    return AnalysisResponse(
        AnalysisRid=str(result["AnalysisRid"]),  # type: ignore[arg-type]
        OutputConfig=OutputConfig(**result["OutputConfig"]),  # type: ignore[arg-type]
    )
