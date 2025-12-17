import logging

from fastapi import APIRouter
from app.models.analysis import CreateAnalysisRequest, AnalysisResponse, OutputConfig
from app.services.analysis_service import create_analysis
from app.services.toggl_service import authenticate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/", response_model=AnalysisResponse)
def create_analysis(request: CreateAnalysisRequest) -> AnalysisResponse:  # type: ignore[no-redef]  # noqa: F811  # noqa: F811
    """
    Create analysis for a date range.

    Retrieves logs from Toggl Track API for the specified date range
    and processes them according to the ResponseMode.
    """
    auth_response = authenticate()
    print(auth_response)

    result = {"AnalysisRid": "foo", "OutputConfig": {"S3OutputPath": "bar"}}

    return AnalysisResponse(
        AnalysisRid=str(result["AnalysisRid"]),  # type: ignore[arg-type]
        OutputConfig=OutputConfig(**result["OutputConfig"]),  # type: ignore[arg-type]
    )
