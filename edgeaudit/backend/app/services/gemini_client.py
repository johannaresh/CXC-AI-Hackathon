"""
Gemini Client — generates human-readable audit narratives
using the Google Gemini API.
"""

from backend.app.core.config import settings
from backend.app.core.logging import logger


def generate_narrative(audit_data: dict) -> str:
    """Generate a natural-language audit narrative via Gemini.

    TODO: Implement actual Gemini API call using google-generativeai.
    TODO: Design prompt template for audit summarisation.
    TODO: Add token-limit handling and retry logic.

    Args:
        audit_data: Dict containing overfit scores, regime analysis,
                    and Monte Carlo results.

    Returns:
        A human-readable narrative string.
    """
    logger.info("Generating narrative via Gemini")

    # --- Stub: uncomment when GEMINI_API_KEY is configured ---
    # import google.generativeai as genai
    # genai.configure(api_key=settings.GEMINI_API_KEY)
    # model = genai.GenerativeModel("gemini-pro")
    # response = model.generate_content(prompt)
    # return response.text

    return (
        f"Audit summary for strategy '{audit_data.get('strategy_name', 'unknown')}': "
        "The strategy shows moderate overfit risk with reasonable regime robustness. "
        "Monte Carlo analysis suggests the observed Sharpe ratio may not be statistically "
        "significant at the 5% level. Further out-of-sample validation is recommended."
    )


def generate_recommendations(audit_data: dict) -> list[str]:
    """Generate actionable recommendations via Gemini.

    TODO: Implement actual Gemini API call.
    TODO: Parse structured recommendations from LLM output.

    Args:
        audit_data: Dict containing full audit results.

    Returns:
        List of recommendation strings.
    """
    # --- Mock implementation ---
    return [
        "Increase out-of-sample test period to at least 2 years.",
        "Reduce the number of free parameters to lower overfit risk.",
        "Test strategy performance across multiple market regimes.",
        "Consider walk-forward optimisation instead of a single train/test split.",
    ]
