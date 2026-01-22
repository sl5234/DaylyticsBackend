import logging
import random
import time
from typing import Any, Dict

from app.config import settings

from openai import OpenAI, RateLimitError  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0


def get_openai_cred() -> str:
    return settings.openai_api_key


def responses(
    model: str,
    input_text: str,
) -> Dict[str, Any]:
    """
    Call OpenAI Responses API with retry on rate limit errors.

    Uses exponential backoff with jitter for retries.

    Args:
        model: Model to use (e.g., "gpt-4.1-mini")
        input_text: Input text/prompt for the LLM

    Returns:
        Response dictionary with output_text from OpenAI API

    Raises:
        RateLimitError: If rate limit is hit after all retries exhausted
    """
    api_key = get_openai_cred()
    client = OpenAI(api_key=api_key)

    last_exception = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            logger.info(f"Calling OpenAI Responses API with model: {model} (attempt {attempt + 1})")
            response = client.responses.create(
                model=model,
                input=input_text,
            )
            return {
                "output_text": response.output_text,
            }
        except RateLimitError as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                # Exponential backoff with jitter
                delay = BASE_DELAY_SECONDS * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1}/{MAX_RETRIES + 1})"
                )
                time.sleep(delay)
            else:
                logger.error(f"Rate limit hit, all {MAX_RETRIES + 1} attempts exhausted")

    raise last_exception  # type: ignore[misc]
