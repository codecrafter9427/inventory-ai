"""Deterministic Stockout Radar risk score (no AI, no certainty claims)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


FORMULA = (
    "risk = clamp(1 - coverage_days / (lead_time_days + safety_stock / avg_daily_movement), 0, 1); "
    "coverage_days = on_hand / avg_daily_movement"
)


def compute_stockout_risk(
    *,
    on_hand: float | Decimal,
    avg_daily_movement: float | Decimal,
    supplier_lead_time_days: float | Decimal,
    safety_stock: float | Decimal,
) -> dict[str, Any]:
    """
    Transparent risk signal from inventory inputs.

    Higher score ⇒ shorter coverage relative to lead time + safety buffer.
    Never claims that a stockout will or will not occur.
    """
    on_hand_f = float(on_hand)
    avg_daily_f = float(avg_daily_movement)
    lead_f = float(supplier_lead_time_days)
    safety_f = float(safety_stock)

    if avg_daily_f <= 0:
        coverage_days = 999.0 if on_hand_f > 0 else 0.0
        risk = 0.0 if on_hand_f > 0 else 1.0
        reasons = [
            "Average daily movement is zero or unavailable; coverage uses a fallback.",
            (
                "With no outbound movement signal, risk is treated as low if stock remains on hand, "
                "otherwise high."
            ),
        ]
        assumptions = [
            "avg_daily_movement <= 0 → coverage_days fallback (999 if on_hand > 0 else 0).",
            "This is a risk signal, not a forecast or certainty claim.",
        ]
    else:
        coverage_days = on_hand_f / avg_daily_f
        buffer_days = lead_f + (safety_f / avg_daily_f)
        if buffer_days <= 0:
            risk = 1.0 if on_hand_f <= 0 else 0.0
            reasons = ["Lead time + safety buffer days is non-positive; fallback risk applied."]
        else:
            raw = 1.0 - (coverage_days / buffer_days)
            risk = max(0.0, min(1.0, raw))
            reasons = []
            if coverage_days < lead_f:
                reasons.append(
                    f"Coverage (~{coverage_days:.1f} days) is shorter than supplier lead time "
                    f"({lead_f:.0f} days)."
                )
            if on_hand_f <= safety_f:
                reasons.append(
                    f"On-hand ({on_hand_f:.2f}) is at or below safety stock ({safety_f:.2f})."
                )
            if risk >= 0.7:
                reasons.append("Risk score is elevated relative to lead-time + safety buffer.")
            elif risk >= 0.4:
                reasons.append("Moderate risk: coverage is only partially above the buffer window.")
            else:
                reasons.append("Coverage appears adequate relative to the stated buffer window.")
        assumptions = [
            "avg_daily_movement is estimated from recent outbound movements (dispatch/sale).",
            "Lead time uses product or supplier catalog days when available.",
            "Safety stock comes from the product catalog.",
            "This is a risk signal, not a prediction that a stockout will occur.",
        ]

    level = "high" if risk >= 0.7 else "medium" if risk >= 0.4 else "low"

    return {
        "risk_score": round(risk, 3),
        "risk_level": level,
        "formula": FORMULA,
        "inputs": {
            "on_hand": round(on_hand_f, 4),
            "avg_daily_movement": round(avg_daily_f, 4),
            "supplier_lead_time_days": round(lead_f, 4),
            "safety_stock": round(safety_f, 4),
            "coverage_days": round(coverage_days, 2),
        },
        "reasons": reasons,
        "assumptions": assumptions,
    }
