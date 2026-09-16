"""
Risk Scoring Utility
====================
Reusable risk scoring logic used throughout ACRIP.
Formula: Risk Score = (Probability × Severity) / 25 × 100
Normalized to 0-100 scale.

Risk Thresholds (configurable):
  LOW      :  0–24
  MEDIUM   : 25–49
  HIGH     : 50–74
  CRITICAL : 75–100

NOTE: In Phase 1.2, the Site Risk Agent will call these utilities
to compute scores from automated sensor/activity data.
"""

from app.models.models import RiskCategory

# ── Configurable thresholds ───────────────────────────────────────────────
RISK_THRESHOLDS = {
    RiskCategory.LOW: (0, 24),
    RiskCategory.MEDIUM: (25, 49),
    RiskCategory.HIGH: (50, 74),
    RiskCategory.CRITICAL: (75, 100),
}


def calculate_risk_score(probability: int, severity: int) -> float:
    """
    Calculate normalized risk score from probability and severity.

    Args:
        probability: 1-5 scale
        severity: 1-5 scale

    Returns:
        Risk score 0-100
    """
    raw = probability * severity  # max = 25
    normalized = (raw / 25) * 100
    return round(normalized, 2)


def get_risk_category(score: float) -> RiskCategory:
    """Return risk category for a given score (0-100 scale)."""
    if score < 25.0:
        return RiskCategory.LOW
    elif score < 50.0:
        return RiskCategory.MEDIUM
    elif score < 75.0:
        return RiskCategory.HIGH
    else:
        return RiskCategory.CRITICAL


def calculate_overall_site_risk(
    environmental: float,
    equipment: float,
    site_condition: float,
    operational: float,
    weights: dict = None,
) -> tuple[float, RiskCategory]:
    """
    Calculate weighted overall site risk from sub-component scores.

    Default weights:
      environmental  : 25%
      equipment      : 30%
      site_condition : 25%
      operational    : 20%

    Returns:
        (overall_score, risk_category)
    """
    if weights is None:
        weights = {
            "environmental": 0.25,
            "equipment": 0.30,
            "site_condition": 0.25,
            "operational": 0.20,
        }

    overall = (
        environmental * weights["environmental"]
        + equipment * weights["equipment"]
        + site_condition * weights["site_condition"]
        + operational * weights["operational"]
    )
    overall = round(overall, 2)
    return overall, get_risk_category(overall)
