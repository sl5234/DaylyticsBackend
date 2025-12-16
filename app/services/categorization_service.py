from typing import List, Dict
from app.models.toggl import TogglTimeEntry
from app.services.llm_service import categorize_with_llm


def categorize_entries(entries: List[TogglTimeEntry], use_llm: bool = False) -> Dict[str, str]:
    """
    Categorize time entries using rule-based or LLM-based approach.
    
    Args:
        entries: List of time entries to categorize
        use_llm: Whether to use LLM for categorization
        
    Returns:
        Dictionary mapping entry IDs to categories
    """
    if use_llm:
        return categorize_with_llm(entries)
    else:
        return _categorize_by_rules(entries)


def _categorize_by_rules(entries: List[TogglTimeEntry]) -> Dict[str, str]:
    """
    Rule-based categorization logic.
    
    Args:
        entries: List of time entries to categorize
        
    Returns:
        Dictionary mapping entry IDs to categories
    """
    # TODO: Implement rule-based categorization
    pass

