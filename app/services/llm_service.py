from typing import List, Dict
from app.models.toggl import TogglTimeEntry
from app.config import settings


def categorize_with_llm(entries: List[TogglTimeEntry]) -> Dict[str, str]:
    """
    Use LLM to categorize time entries.
    
    Args:
        entries: List of time entries to categorize
        
    Returns:
        Dictionary mapping entry IDs to categories
    """
    # TODO: Implement LLM categorization
    pass

