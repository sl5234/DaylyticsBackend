import logging

from fastapi import APIRouter
from appdevcommons.unique_id import UniqueIdGenerator  # type: ignore[import-untyped]
from app.models.analysis import (
    CreateAnalysisRequest,
    CreateAnalysisResponse,
    OutputConfig,
    ResponseMode,
)
from app.agents.analyzers.metric_generator import generate_all_metrics
from app.agents.analyzers.table_generator import generate_table
from app.agents.analyzers.summarizer import generate_summary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/", response_model=CreateAnalysisResponse)
def create_analysis(request: CreateAnalysisRequest) -> CreateAnalysisResponse:  # type: ignore[no-redef]  # noqa: F811  # noqa: F811
    logger.info(f"Creating analysis with mode: {request.response_mode}")

    if request.response_mode == ResponseMode.METRIC:
        logger.info("Generating metrics from activity logs")
        all_metrics = generate_all_metrics(request.prompt, request.activity_logs)
        logger.info(f"Generated {len(all_metrics)} metrics")

    elif request.response_mode == ResponseMode.TABLE:
        logger.info("Generating table from activity logs")
        table = generate_table(request.activity_logs)
        logger.info(f"Generated table with {len(table)} rows")

    elif request.response_mode == ResponseMode.TEXT:
        logger.info("Generating text summary from activity logs")
        summary = generate_summary(request.activity_logs)
        logger.info(f"Generated summary with {len(summary)} characters")

    id_generator = UniqueIdGenerator()
    analysis_rid = id_generator.generate_id()

    s3_output_path = f"s3://daylytics/analysis/{analysis_rid}/output"

    return CreateAnalysisResponse(
        analysis_rid=str(analysis_rid),  # type: ignore[arg-type]
        output_config=OutputConfig(s3_output_path=s3_output_path),
    )
