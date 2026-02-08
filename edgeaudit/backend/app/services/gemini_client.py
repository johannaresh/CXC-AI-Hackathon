"""
Gemini Client — generates human-readable audit narratives and
actionable recommendations using the Google Gemini API.
"""

import json

from ..core.config import settings
from ..core.logging import logger

NARRATIVE_PROMPT = """You are EdgeAudit, an AI-powered quantitative strategy auditing assistant.
Your role is to protect retail investors by clearly explaining the risks and strengths of
a trading strategy's backtest results.

You have been given the following audit data for a strategy called "{strategy_name}":{asset_context}

## Overfit Detection
- Overfit Probability: {overfit_probability:.1%} (Label: {overfit_label})
- Confidence in this assessment: {overfit_confidence:.1%}

## Regime Analysis
- Current detected regime: {current_regime}
- Regime sensitivity score: {regime_sensitivity:.2f} (0=robust, 1+=fragile)
- Per-regime Sharpe ratios: {per_regime_sharpe}
- Worst-case regime Sharpe: {worst_regime_sharpe}

## Monte Carlo Statistical Test
- Observed backtest Sharpe: {observed_sharpe}
- Simulated Sharpe mean (bootstrap): {mc_sharpe_mean:.3f}
- Simulated Sharpe std: {mc_sharpe_std:.3f}
- P-value (observed vs null): {mc_p_value:.4f}
- 95% Confidence Interval: [{ci_lower:.3f}, {ci_upper:.3f}]

## Edge Score: {edge_score}/100
- Overfit sub-score: {overfit_sub}/100
- Regime sub-score: {regime_sub}/100
- Statistical significance sub-score: {stat_sig_sub}/100
- Data leakage sub-score: {leakage_sub}/100
- Explainability sub-score: {explain_sub}/100

## Strategy Metadata
- Parameters: {num_parameters}
- Sample size: {sample_size} periods
- Train/test split: {train_test_ratio:.0%}/{test_ratio:.0%}
- Rebalance frequency: {rebalance_frequency}

Write a 3-4 paragraph audit narrative that:
1. Opens with the Edge Score and an overall assessment in plain language.
2. Explains the most concerning finding in detail (use the specific numbers).
3. Highlights any strengths.
4. Closes with a clear, actionable conclusion for a retail investor.

Use a professional but accessible tone. Avoid jargon where possible. When you must use
technical terms (Sharpe ratio, p-value), briefly define them in parentheses.
Do NOT use markdown formatting. Write in plain prose paragraphs."""

RECOMMENDATIONS_PROMPT = """Based on the following EdgeAudit results for strategy "{strategy_name}":

Edge Score: {edge_score}/100
Overfit probability: {overfit_probability:.1%}
Regime sensitivity: {regime_sensitivity:.2f}
Monte Carlo p-value: {mc_p_value:.4f}
Parameter count: {num_parameters}
Sample size: {sample_size}
Train/test split: {train_test_ratio}
{asset_context_recs}
Generate exactly 5 specific, actionable recommendations for improving this strategy's
robustness and reducing overfitting risk.

Format your response as a JSON array of exactly 5 strings. Each recommendation should be
one sentence, specific to the numbers above. Example format:
["Recommendation 1", "Recommendation 2", "Recommendation 3", "Recommendation 4", "Recommendation 5"]

Respond with ONLY the JSON array, no other text."""


def _flatten_audit_data(audit_data: dict) -> dict:
    """Flatten nested audit data into a single-level dict for prompt formatting."""
    overfit = audit_data.get("overfit", {})
    regime = audit_data.get("regime", {})
    mc = audit_data.get("monte_carlo", {})
    edge = audit_data.get("edge_score", {})
    payload = audit_data.get("payload", {})
    selected_asset = audit_data.get("selected_asset")

    ci = mc.get("confidence_interval_95", [0.0, 0.0])
    train_ratio = payload.get("train_test_split_ratio", 0.7)

    # Add asset context if a specific asset was selected
    asset_context = ""
    asset_context_recs = ""
    if selected_asset:
        asset_context = f"\n\n## Asset Being Audited\n- Ticker: {selected_asset}\n- This audit focuses specifically on {selected_asset} within the strategy's universe.\n"
        asset_context_recs = f"\nAsset being audited: {selected_asset}\n"

    return {
        "strategy_name": audit_data.get("strategy_name", "unknown"),
        "overfit_probability": overfit.get("probability", 0.5),
        "overfit_label": overfit.get("label", "medium"),
        "overfit_confidence": overfit.get("confidence", 0.0),
        "current_regime": regime.get("current_regime", "unknown"),
        "regime_sensitivity": regime.get("regime_sensitivity", 0.0),
        "per_regime_sharpe": regime.get("per_regime_sharpe", {}),
        "worst_regime_sharpe": regime.get("worst_regime_sharpe", 0.0),
        "observed_sharpe": payload.get("backtest_sharpe", 0.0),
        "mc_sharpe_mean": mc.get("simulated_sharpe_mean", 0.0),
        "mc_sharpe_std": mc.get("simulated_sharpe_std", 0.0),
        "mc_p_value": mc.get("p_value", 1.0),
        "ci_lower": ci[0] if len(ci) > 0 else 0.0,
        "ci_upper": ci[1] if len(ci) > 1 else 0.0,
        "edge_score": edge.get("edge_score", 0.0),
        "overfit_sub": edge.get("overfit_sub_score", 0.0),
        "regime_sub": edge.get("regime_sub_score", 0.0),
        "stat_sig_sub": edge.get("stat_sig_sub_score", 0.0),
        "leakage_sub": edge.get("data_leakage_sub_score", 0.0),
        "explain_sub": edge.get("explainability_sub_score", 0.0),
        "num_parameters": payload.get("num_parameters", 0),
        "sample_size": len(payload.get("raw_returns", [])),
        "train_test_ratio": train_ratio,
        "test_ratio": 1.0 - train_ratio,
        "rebalance_frequency": payload.get("rebalance_frequency", "monthly"),
        "asset_context": asset_context,
        "asset_context_recs": asset_context_recs,
    }


def is_configured() -> bool:
    """Check if Gemini API key is configured."""
    return bool(settings.GEMINI_API_KEY)


def _get_model():
    """Initialize Gemini model."""
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")


def generate_narrative(audit_data: dict) -> str:
    """Generate a natural-language audit narrative via Gemini.

    Falls back to template-based narrative if Gemini is unavailable.
    """
    logger.info("Generating narrative via Gemini")

    if not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY configured, returning fallback narrative")
        return _fallback_narrative(audit_data)

    try:
        import google.generativeai as genai
        model = _get_model()
        flat = _flatten_audit_data(audit_data)
        prompt = NARRATIVE_PROMPT.format(**flat)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        return response.text
    except Exception as e:
        logger.error("Gemini narrative generation failed: %s", e)
        return _fallback_narrative(audit_data)


def generate_recommendations(audit_data: dict) -> list[str]:
    """Generate actionable recommendations via Gemini.

    Falls back to static recommendations if Gemini is unavailable.
    """
    if not settings.GEMINI_API_KEY:
        return _fallback_recommendations()

    try:
        import google.generativeai as genai
        model = _get_model()
        flat = _flatten_audit_data(audit_data)
        prompt = RECOMMENDATIONS_PROMPT.format(**flat)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=512,
            ),
        )

        # Parse JSON array from response
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()

        recommendations = json.loads(text)
        if isinstance(recommendations, list) and len(recommendations) >= 3:
            return [str(r) for r in recommendations[:5]]
    except Exception as e:
        logger.error("Gemini recommendations generation failed: %s", e)

    return _fallback_recommendations()


def _fallback_narrative(audit_data: dict) -> str:
    """Template-based fallback narrative when Gemini is unavailable."""
    flat = _flatten_audit_data(audit_data)
    name = flat["strategy_name"]
    score = flat["edge_score"]
    overfit_prob = flat["overfit_probability"]
    p_value = flat["mc_p_value"]
    regime_sens = flat["regime_sensitivity"]

    if score >= 70:
        assessment = "shows promising indicators of genuine statistical edge"
    elif score >= 40:
        assessment = "presents mixed signals requiring further investigation"
    else:
        assessment = "raises significant concerns about overfitting and robustness"

    return (
        f"Strategy '{name}' received an Edge Score of {score:.0f}/100, which {assessment}. "
        f"The overfit detection model estimates a {overfit_prob:.0%} probability that this "
        f"strategy's backtest performance is a result of overfitting rather than genuine predictive power. "
        f"Monte Carlo bootstrap testing produced a p-value of {p_value:.3f}, meaning "
        f"{'the observed performance is statistically significant' if p_value < 0.05 else 'the observed performance may not be statistically distinguishable from random chance'}. "
        f"Regime analysis indicates a sensitivity score of {regime_sens:.2f}, "
        f"{'suggesting robust performance across market conditions' if regime_sens < 0.5 else 'indicating the strategy may be fragile to changing market conditions'}. "
        f"Retail investors should carefully consider these findings before allocating capital."
    )


def _fallback_recommendations() -> list[str]:
    """Static fallback recommendations."""
    return [
        "Increase out-of-sample test period to at least 2 years.",
        "Reduce the number of free parameters to lower overfit risk.",
        "Test strategy performance across multiple market regimes.",
        "Consider walk-forward optimization instead of a single train/test split.",
        "Verify that no future data leaks into the training period.",
    ]
