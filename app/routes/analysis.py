from fastapi import APIRouter
from app.models.analysis import CreateAnalysisRequest, AnalysisResponse
from app.services.analysis_service import create_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/", response_model=AnalysisResponse)
def create_analysis_endpoint(request: CreateAnalysisRequest) -> AnalysisResponse:
    """
    Create analysis for a given day.
    
    Retrieves logs from Toggl Track API, categorizes them,
    and emits metrics to configured backend.
    """
    result = create_analysis(request.date, use_llm=request.use_llm)
    
    return AnalysisResponse(
        status=result["status"],
        date=request.date,
        metrics=result["metrics"],
        categories=result["categories"]
    )

