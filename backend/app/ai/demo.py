"""Deterministic DemoAIProvider — works without Ollama or any paid API."""

from typing import Any

from app.ai.provider import AIProvider


class DemoAIProvider(AIProvider):
    """Fixed, explainable stub responses for local demos."""

    async def reorder_recommendations(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sku = input_payload.get("sku", "DEMO-SKU")
        return {
            "result": {
                "sku": sku,
                "recommended_qty": 24,
                "assumptions": [
                    "Average daily movement assumed at 2 units (demo).",
                    "Supplier lead time assumed at 7 days (demo).",
                    "Reorder point assumed from catalog (demo).",
                ],
                "provider": "demo",
            },
            "explanation": (
                "Demo reorder recommendation: order 24 units to cover lead time "
                "plus a small buffer. Not based on live ledger data."
            ),
            "sources": [{"type": "demo", "id": "seed-placeholder", "label": "Demo catalog"}],
            "requires_confirmation": True,
        }

    async def inventory_question(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        question = input_payload.get("question", "")
        return {
            "result": {
                "answer": (
                    f"Demo answer for: {question or '(empty question)'}. "
                    "Allowlisted read tools are not wired yet."
                ),
                "provider": "demo",
            },
            "explanation": "Deterministic demo response; no model was called.",
            "sources": [],
            "requires_confirmation": False,
        }

    async def stockout_radar(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        product_id = input_payload.get("product_id", "demo-product")
        # Transparent demo score — formula documented, not a certainty claim
        on_hand = float(input_payload.get("on_hand", 10))
        avg_daily = float(input_payload.get("avg_daily_movement", 2))
        lead_time = float(input_payload.get("supplier_lead_time_days", 7))
        safety = float(input_payload.get("safety_stock", 5))
        coverage_days = on_hand / avg_daily if avg_daily > 0 else 999.0
        risk = max(0.0, min(1.0, 1.0 - (coverage_days / (lead_time + safety / max(avg_daily, 0.1)))))
        return {
            "result": {
                "product_id": product_id,
                "risk_score": round(risk, 3),
                "formula": (
                    "risk = clamp(1 - coverage_days / (lead_time_days + safety_stock/avg_daily), 0, 1); "
                    "coverage_days = on_hand / avg_daily_movement"
                ),
                "inputs": {
                    "on_hand": on_hand,
                    "avg_daily_movement": avg_daily,
                    "supplier_lead_time_days": lead_time,
                    "safety_stock": safety,
                    "coverage_days": round(coverage_days, 2),
                },
                "provider": "demo",
            },
            "explanation": (
                "Stockout Radar demo score from transparent inputs. "
                "This is a risk signal, not a prediction of stockout certainty."
            ),
            "sources": [{"type": "demo", "id": str(product_id), "label": "Demo inputs"}],
            "requires_confirmation": False,
        }
