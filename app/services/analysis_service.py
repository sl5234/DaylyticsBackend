from datetime import date
from typing import Dict, Any
from app.models.toggl import TogglDailyLogs
from app.models.metrics import MetricsData
from app.services.toggl_service import get_daily_logs
from app.services.categorization_service import categorize_entries
from app.services.metrics_service import emit_metrics


def create_analysis(target_date: date, use_llm: bool = False) -> Dict[str, Any]:
    """
    Create analysis for a given day:
    1. Fetch logs from Toggl Track API
    2. Categorize entries (rule-based or LLM)
    3. Emit metrics to configured backend
    
    Args:
        target_date: The date to analyze
        use_llm: Whether to use LLM for categorization
        
    Returns:
        Dictionary containing analysis results
    """
    # Step 1: Get daily logs from Toggl
    daily_logs = get_daily_logs(target_date)
    
    # Step 2: Categorize entries
    categories = categorize_entries(daily_logs.entries, use_llm=use_llm)
    
    # Step 3: Prepare metrics data
    metrics_data = _prepare_metrics_data(target_date, daily_logs, categories)
    
    # Step 4: Emit metrics
    emit_metrics(metrics_data)
    
    return {
        "status": "success",
        "date": target_date,
        "metrics": metrics_data.model_dump(),
        "categories": categories
    }


def _prepare_metrics_data(target_date: date, logs: TogglDailyLogs, categories: Dict[str, str]) -> MetricsData:
    """
    Prepare metrics data from logs and categories.
    
    Args:
        target_date: The date being analyzed
        logs: The daily logs from Toggl
        categories: The categorized entries
        
    Returns:
        MetricsData object ready for emission
    """
    # TODO: Calculate category totals, total hours, etc.
    pass

