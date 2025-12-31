import logging
from typing import Any, Dict

from app.config import settings

from openai import OpenAI  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def get_openai_cred() -> str:
    return settings.openai_api_key


def responses(
    model: str,
    input_text: str,
) -> Dict[str, Any]:
    """
    Call OpenAI Responses API.

    Args:
        model: Model to use (e.g., "gpt-4.1-mini")
        input_text: Input text/prompt for the LLM

    Returns:
        Response dictionary with output_text from OpenAI API
    """
    api_key = get_openai_cred()
    client = OpenAI(api_key=api_key)

    logger.info(f"Calling OpenAI Responses API with model: {model}")
    response = client.responses.create(
        model=model,
        input=input_text,
    )

    return {
        "output_text": response.output_text,
    }
