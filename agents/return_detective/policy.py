"""
Return Detective — Policy Guardrails Engine
Pure deterministic Python function enforcing safety tiers according to CONTEXT.md:
  - auto: confidence >= 0.8 AND reversible AND rupee impact < 5000
  - approve: needs one tap from store manager (Google Chat card or web app)
  - recommend: shown to the owner only
"""

from typing import Literal

ActionTier = Literal["auto", "approve", "recommend"]

def decide_tier(
    action_type: str,
    confidence: float,
    reversible: bool,
    rupee_impact: float
) -> ActionTier:
    """
    Deterministic safety policy:
    1. Auto: confidence >= 0.8 AND reversible AND rupee_impact < 5,000 INR
    2. Recommend: Irreversible strategic decisions OR rupee impact >= 50,000 INR
    3. Approve: Everything else requiring store manager confirmation
    """
    confidence = float(confidence)
    rupee_impact = float(rupee_impact)
    reversible = bool(reversible)

    # Strategic owner recommendations (high financial stakes or permanent account termination)
    if rupee_impact >= 50000.0 or action_type in ("supplier_contract_termination", "permanent_account_ban"):
        return "recommend"

    # Autonomous execution guardrails
    if confidence >= 0.80 and reversible and rupee_impact < 5000.0:
        return "auto"

    # Default to store manager one-tap approval
    return "approve"
