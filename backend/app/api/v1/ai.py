"""AI endpoints — reorder, Q&A, Stockout Radar, draft-PO confirm (auth required)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.tools import InventoryReadTools, select_tools_for_question
from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context, get_provider
from app.errors import http_error
from app.models import Product
from app.permissions import CATALOG_ROLES, require_roles
from app.schemas.ai import (
    AIResultEnvelope,
    ConfirmDraftPORequest,
    InventoryQuestionRequest,
    ReorderRecommendationsRequest,
    StockoutRadarRequest,
)
from app.schemas.common import AIResultEnvelope as LegacyEnvelope
from app.services.draft_po import create_draft_po_from_recommendations
from app.services.inventory_signals import build_product_signal, list_product_signals
from app.services.stockout_radar import FORMULA, compute_stockout_risk

router = APIRouter(prefix="/ai", tags=["ai"])


def _signal_dict(signal: Any) -> dict[str, Any]:
    return {
        "product_id": str(signal.product_id),
        "sku": signal.sku,
        "name": signal.name,
        "on_hand": str(signal.on_hand),
        "avg_daily_movement": str(signal.avg_daily_movement),
        "lead_time_days": signal.lead_time_days,
        "reorder_point": str(signal.reorder_point),
        "safety_stock": str(signal.safety_stock),
        "recommended_qty": str(signal.recommended_qty),
        "below_reorder_point": signal.below_reorder_point,
        "movement_days_observed": signal.movement_days_observed,
        "assumptions": signal.assumptions,
    }


@router.post("/reorder-recommendations", response_model=LegacyEnvelope)
async def reorder_recommendations(
    body: ReorderRecommendationsRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_provider),
) -> dict[str, Any]:
    """Recommend reorder qty from movement / stock / lead time / reorder point."""
    signals = list_product_signals(
        db,
        organization_id=auth.organization_id,
        product_ids=body.product_ids or None,
        only_actionable=body.only_actionable,
        lookback_days=body.lookback_days,
        limit=body.limit,
    )
    recommendations = [_signal_dict(s) for s in signals]
    envelope = await provider.reorder_recommendations(
        input_payload={
            "recommendations": recommendations,
            "lookback_days": body.lookback_days,
            "organization_id": str(auth.organization_id),
        },
        context_ids=[str(s.product_id) for s in signals],
        options={},
    )
    # Ensure structured recommendations always present (deterministic core)
    envelope["result"]["recommendations"] = recommendations
    envelope["result"]["labeled_ai"] = True
    envelope["requires_confirmation"] = True
    return AIResultEnvelope.model_validate(envelope).model_dump()


@router.post("/inventory-question", response_model=LegacyEnvelope)
async def inventory_question(
    body: InventoryQuestionRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_provider),
) -> dict[str, Any]:
    """Natural-language inventory Q&A via allowlisted read tools only."""
    tools = InventoryReadTools(db, organization_id=auth.organization_id)
    planned = select_tools_for_question(body.question)
    tool_results = [tools.invoke(name, args) for name, args in planned]

    envelope = await provider.inventory_question(
        input_payload={
            "question": body.question,
            "tool_results": tool_results,
            "organization_id": str(auth.organization_id),
        },
        context_ids=[],
        options={"tools": tools},
    )
    envelope["result"]["tools_used"] = [name for name, _ in planned]
    envelope["result"]["tool_results"] = tool_results
    envelope["result"]["labeled_ai"] = True
    envelope["requires_confirmation"] = False
    return AIResultEnvelope.model_validate(envelope).model_dump()


@router.post("/stockout-radar", response_model=LegacyEnvelope)
async def stockout_radar(
    body: StockoutRadarRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_provider),
) -> dict[str, Any]:
    """Differentiator: transparent risk score with formula, reasons, assumptions."""
    # Manual override path (formula unit demos)
    if (
        body.on_hand is not None
        and body.avg_daily_movement is not None
        and body.supplier_lead_time_days is not None
        and body.safety_stock is not None
    ):
        radar = compute_stockout_risk(
            on_hand=body.on_hand,
            avg_daily_movement=body.avg_daily_movement,
            supplier_lead_time_days=body.supplier_lead_time_days,
            safety_stock=body.safety_stock,
        )
        items = [
            {
                "product_id": str(body.product_id) if body.product_id else "manual",
                "sku": "MANUAL",
                "name": "Manual inputs",
                **radar,
            }
        ]
    elif body.product_id is not None:
        product = (
            db.query(Product)
            .filter(
                Product.id == body.product_id,
                Product.organization_id == auth.organization_id,
            )
            .one_or_none()
        )
        if product is None:
            raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Product not found")
        signal = build_product_signal(
            db,
            organization_id=auth.organization_id,
            product=product,
            lookback_days=body.lookback_days,
        )
        radar = compute_stockout_risk(
            on_hand=signal.on_hand,
            avg_daily_movement=signal.avg_daily_movement,
            supplier_lead_time_days=signal.lead_time_days,
            safety_stock=signal.safety_stock,
        )
        items = [
            {
                "product_id": str(signal.product_id),
                "sku": signal.sku,
                "name": signal.name,
                **radar,
            }
        ]
    else:
        signals = list_product_signals(
            db,
            organization_id=auth.organization_id,
            only_actionable=False,
            lookback_days=body.lookback_days,
            limit=body.limit,
        )
        items = []
        for signal in signals:
            radar = compute_stockout_risk(
                on_hand=signal.on_hand,
                avg_daily_movement=signal.avg_daily_movement,
                supplier_lead_time_days=signal.lead_time_days,
                safety_stock=signal.safety_stock,
            )
            items.append(
                {
                    "product_id": str(signal.product_id),
                    "sku": signal.sku,
                    "name": signal.name,
                    "on_hand": str(signal.on_hand),
                    **radar,
                }
            )
        items.sort(key=lambda row: float(row["risk_score"]), reverse=True)

    envelope = await provider.stockout_radar(
        input_payload={"items": items, "organization_id": str(auth.organization_id)},
        context_ids=[str(i.get("product_id")) for i in items],
        options={},
    )
    envelope["result"]["items"] = items
    envelope["result"]["formula"] = FORMULA
    envelope["result"]["labeled_ai"] = True
    envelope["requires_confirmation"] = False
    return AIResultEnvelope.model_validate(envelope).model_dump()


@router.post("/confirm-draft-po", response_model=LegacyEnvelope)
async def confirm_draft_po(
    body: ConfirmDraftPORequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a draft purchase order after explicit user confirmation.

    Never updates stock balances. Requires confirm=true and catalog roles.
    """
    require_roles(auth, CATALOG_ROLES, action="confirm AI draft purchase orders")
    if not body.confirm:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "confirmation_required",
            "Set confirm=true after reviewing AI recommendations. No PO was created.",
        )
    if not body.lines:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "At least one confirmed line is required",
        )

    try:
        po = create_draft_po_from_recommendations(
            db,
            organization_id=auth.organization_id,
            actor_user_id=auth.user_id,
            lines=[ln.model_dump() for ln in body.lines],
            supplier_id=body.supplier_id,
            location_id=body.location_id,
            notes=body.notes,
        )
    except ValueError as exc:
        raise http_error(
            status.HTTP_400_BAD_REQUEST,
            "draft_po_failed",
            str(exc),
        ) from exc

    return {
        "result": {
            "purchase_order_id": str(po.id),
            "po_number": po.po_number,
            "status": po.status,
            "supplier_name": po.supplier.name if po.supplier else None,
            "location_name": po.location.name if po.location else None,
            "line_count": len(po.lines),
            "labeled_ai": True,
            "stock_changed": False,
        },
        "explanation": (
            f"Draft purchase order {po.po_number} created after user confirmation. "
            "Stock was not changed."
        ),
        "sources": [
            {"type": "purchase_order", "id": str(po.id), "label": po.po_number},
        ],
        "requires_confirmation": False,
    }
