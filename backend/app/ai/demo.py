"""Deterministic DemoAIProvider — works offline without Ollama or paid APIs."""

from __future__ import annotations

from typing import Any

from app.ai.provider import AIProvider
from app.ai.tools import InventoryReadTools, select_tools_for_question
from app.services.stockout_radar import FORMULA, compute_stockout_risk


class DemoAIProvider(AIProvider):
    """Explainable, deterministic responses over precomputed / tool-backed context."""

    async def reorder_recommendations(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        recommendations = input_payload.get("recommendations") or []
        # If caller already computed signals, narrate them; else use demo singleton
        if not recommendations:
            sku = input_payload.get("sku", "DEMO-SKU")
            recommendations = [
                {
                    "sku": sku,
                    "recommended_qty": "24",
                    "assumptions": [
                        "Average daily movement assumed at 2 units (demo fallback).",
                        "Supplier lead time assumed at 7 days (demo fallback).",
                    ],
                }
            ]
        count = len(recommendations)
        top = recommendations[0] if recommendations else {}
        explanation = (
            f"DemoAIProvider: {count} reorder candidate(s) from stock, movement, lead time, "
            f"and reorder point. Top suggestion: {top.get('sku', 'n/a')} × "
            f"{top.get('recommended_qty', 0)}. AI never changes stock; confirm to draft a PO."
        )
        sources = [
            {"type": "recommendation", "id": str(r.get("product_id", r.get("sku", i))), "label": str(r.get("sku", "item"))}
            for i, r in enumerate(recommendations[:10])
        ]
        if not sources:
            sources = [{"type": "demo", "id": "seed-placeholder", "label": "Demo catalog"}]
        return {
            "result": {
                "recommendations": recommendations,
                "provider": "demo",
                "context_ids": context_ids or [],
            },
            "explanation": explanation,
            "sources": sources,
            "requires_confirmation": True,
        }

    async def inventory_question(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        question = str(input_payload.get("question", "")).strip()
        tool_results = input_payload.get("tool_results")
        if tool_results is None and options and options.get("tools") is not None:
            tools: InventoryReadTools = options["tools"]
            planned = select_tools_for_question(question)
            tool_results = [tools.invoke(name, args) for name, args in planned]
            tools_used = [name for name, _ in planned]
        else:
            tool_results = tool_results or []
            tools_used = [r.get("tool", "unknown") for r in tool_results if isinstance(r, dict)]

        answer = _compose_answer(question, tool_results)
        sources = []
        for result in tool_results:
            if not isinstance(result, dict):
                continue
            tool = str(result.get("tool", "tool"))
            items = result.get("items") or []
            if isinstance(items, list) and items:
                first = items[0]
                label = first.get("sku") or first.get("po_number") or tool
                sources.append({"type": tool, "id": str(first.get("product_id") or first.get("id") or tool), "label": str(label)})
            else:
                sources.append({"type": tool, "id": tool, "label": tool})

        return {
            "result": {
                "answer": answer,
                "tools_used": tools_used,
                "tool_results": tool_results,
                "provider": "demo",
                "labeled_ai": True,
            },
            "explanation": (
                "Deterministic DemoAIProvider answer from allowlisted read tools only. "
                "Not certified inventory advice."
            ),
            "sources": sources[:10],
            "requires_confirmation": False,
        }

    async def stockout_radar(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        items = input_payload.get("items")
        if items:
            top = items[0]
            explanation = (
                f"Stockout Radar (demo narration): highest listed risk is "
                f"{top.get('sku', 'item')} at score {top.get('risk_score', 'n/a')}. "
                "Scores are transparent risk signals, not stockout predictions."
            )
            return {
                "result": {
                    "items": items,
                    "formula": FORMULA,
                    "provider": "demo",
                    "labeled_ai": True,
                },
                "explanation": explanation,
                "sources": [
                    {
                        "type": "product",
                        "id": str(it.get("product_id", it.get("sku", i))),
                        "label": str(it.get("sku", "product")),
                    }
                    for i, it in enumerate(items[:10])
                ],
                "requires_confirmation": False,
            }

        # Manual / unit-test path: compute from raw inputs
        product_id = input_payload.get("product_id", "demo-product")
        on_hand = float(input_payload.get("on_hand", 10))
        avg_daily = float(input_payload.get("avg_daily_movement", 2))
        lead_time = float(input_payload.get("supplier_lead_time_days", 7))
        safety = float(input_payload.get("safety_stock", 5))
        radar = compute_stockout_risk(
            on_hand=on_hand,
            avg_daily_movement=avg_daily,
            supplier_lead_time_days=lead_time,
            safety_stock=safety,
        )
        return {
            "result": {
                "product_id": product_id,
                **radar,
                "provider": "demo",
                "labeled_ai": True,
            },
            "explanation": (
                "Stockout Radar score from transparent inputs. "
                "This is a risk signal, not a prediction of stockout certainty."
            ),
            "sources": [{"type": "inputs", "id": str(product_id), "label": "Radar inputs"}],
            "requires_confirmation": False,
        }


def _compose_answer(question: str, tool_results: list[Any]) -> str:
    parts = [f"AI-generated answer for: {question or '(empty)'}."]
    for result in tool_results:
        if not isinstance(result, dict):
            continue
        tool = result.get("tool")
        if result.get("error"):
            parts.append(f"{tool}: {result['error']}.")
            continue
        if tool == "list_low_stock":
            items = result.get("items") or []
            if not items:
                parts.append("No products are currently at or below reorder point.")
            else:
                sample = ", ".join(f"{i['sku']} (on hand {i['on_hand']})" for i in items[:5])
                parts.append(f"Low-stock items ({len(items)}): {sample}.")
        elif tool == "list_reorder_candidates":
            items = result.get("items") or []
            if not items:
                parts.append("No reorder candidates with positive recommended quantity.")
            else:
                sample = ", ".join(
                    f"{i['sku']}→{i['recommended_qty']}" for i in items[:5]
                )
                parts.append(f"Reorder candidates: {sample}. Confirm before drafting a PO.")
        elif tool == "list_open_purchase_orders":
            items = result.get("items") or []
            if not items:
                parts.append("No open purchase orders (draft/ordered/partial).")
            else:
                sample = ", ".join(f"{i['po_number']} ({i['status']})" for i in items[:5])
                parts.append(f"Open POs: {sample}.")
        elif tool == "get_recent_movements":
            items = result.get("items") or []
            parts.append(f"Recent movements returned: {len(items)} row(s).")
        elif tool == "get_product_stock":
            parts.append(
                f"{result.get('sku')} on-hand total {result.get('on_hand_total')} "
                f"(reorder point {result.get('reorder_point')})."
            )
        elif tool == "get_stockout_radar":
            items = result.get("items") or []
            if items:
                top = items[0]
                parts.append(
                    f"Highest listed radar score: {top.get('sku')} = {top.get('risk_score')} "
                    f"({top.get('risk_level')}). Not a certainty claim."
                )
    parts.append("Sources are organization-scoped read tools only.")
    return " ".join(parts)
