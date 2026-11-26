"""Allowlisted, org-scoped read tools for inventory Q&A (no arbitrary SQL)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy.orm import Session, joinedload

from app.models import Product, PurchaseOrder, StockBalance, StockMovement
from app.services.inventory_signals import (
    LOOKBACK_DAYS_DEFAULT,
    build_product_signal,
    list_product_signals,
    sum_on_hand,
)
from app.services.stockout_radar import compute_stockout_risk

ToolFn = Callable[..., dict[str, Any]]


ALLOWED_TOOLS: frozenset[str] = frozenset(
    {
        "list_low_stock",
        "get_product_stock",
        "get_recent_movements",
        "list_open_purchase_orders",
        "get_stockout_radar",
        "list_reorder_candidates",
    }
)


class InventoryReadTools:
    """Typed business tools. Organization authorization must be applied by the caller."""

    def __init__(self, db: Session, *, organization_id: uuid.UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    def list_low_stock(self, *, limit: int = 15) -> dict[str, Any]:
        limit = max(1, min(int(limit), 50))
        products = (
            self.db.query(Product)
            .filter(
                Product.organization_id == self.organization_id,
                Product.is_active.is_(True),
                Product.archived_at.is_(None),
            )
            .order_by(Product.sku.asc())
            .limit(200)
            .all()
        )
        rows: list[dict[str, Any]] = []
        for product in products:
            on_hand = sum_on_hand(
                self.db,
                organization_id=self.organization_id,
                product_id=product.id,
            )
            rp = product.reorder_point or Decimal("0")
            if on_hand <= rp:
                rows.append(
                    {
                        "product_id": str(product.id),
                        "sku": product.sku,
                        "name": product.name,
                        "on_hand": str(on_hand),
                        "reorder_point": str(rp),
                    }
                )
            if len(rows) >= limit:
                break
        return {"tool": "list_low_stock", "items": rows, "count": len(rows)}

    def get_product_stock(self, *, sku: str | None = None, product_id: str | None = None) -> dict[str, Any]:
        query = self.db.query(Product).filter(
            Product.organization_id == self.organization_id,
            Product.is_active.is_(True),
        )
        if product_id:
            query = query.filter(Product.id == uuid.UUID(str(product_id)))
        elif sku:
            query = query.filter(Product.sku.ilike(sku.strip()))
        else:
            return {"tool": "get_product_stock", "error": "sku or product_id required"}
        product = query.one_or_none()
        if product is None:
            return {"tool": "get_product_stock", "error": "product_not_found"}
        balances = (
            self.db.query(StockBalance)
            .options(joinedload(StockBalance.location))
            .filter(
                StockBalance.organization_id == self.organization_id,
                StockBalance.product_id == product.id,
            )
            .all()
        )
        return {
            "tool": "get_product_stock",
            "product_id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "reorder_point": str(product.reorder_point),
            "safety_stock": str(product.safety_stock),
            "lead_time_days": product.lead_time_days,
            "on_hand_total": str(
                sum_on_hand(self.db, organization_id=self.organization_id, product_id=product.id)
            ),
            "balances": [
                {
                    "location": bal.location.code if bal.location else None,
                    "quantity": str(bal.quantity),
                }
                for bal in balances
            ],
        }

    def get_recent_movements(self, *, limit: int = 10, sku: str | None = None) -> dict[str, Any]:
        limit = max(1, min(int(limit), 50))
        query = (
            self.db.query(StockMovement)
            .options(joinedload(StockMovement.product), joinedload(StockMovement.location))
            .filter(StockMovement.organization_id == self.organization_id)
        )
        if sku:
            product = (
                self.db.query(Product)
                .filter(
                    Product.organization_id == self.organization_id,
                    Product.sku.ilike(sku.strip()),
                )
                .one_or_none()
            )
            if product is None:
                return {"tool": "get_recent_movements", "items": [], "error": "product_not_found"}
            query = query.filter(StockMovement.product_id == product.id)
        rows = query.order_by(StockMovement.created_at.desc()).limit(limit).all()
        return {
            "tool": "get_recent_movements",
            "items": [
                {
                    "id": str(m.id),
                    "sku": m.product.sku if m.product else None,
                    "location": m.location.code if m.location else None,
                    "movement_type": m.movement_type,
                    "quantity": str(m.quantity),
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in rows
            ],
        }

    def list_open_purchase_orders(self, *, limit: int = 10) -> dict[str, Any]:
        limit = max(1, min(int(limit), 50))
        rows = (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.supplier))
            .filter(
                PurchaseOrder.organization_id == self.organization_id,
                PurchaseOrder.status.in_(("draft", "ordered", "partially_received")),
            )
            .order_by(PurchaseOrder.po_number.desc())
            .limit(limit)
            .all()
        )
        return {
            "tool": "list_open_purchase_orders",
            "items": [
                {
                    "id": str(po.id),
                    "po_number": po.po_number,
                    "status": po.status,
                    "supplier": po.supplier.name if po.supplier else None,
                }
                for po in rows
            ],
        }

    def get_stockout_radar(self, *, sku: str | None = None, limit: int = 10) -> dict[str, Any]:
        limit = max(1, min(int(limit), 50))
        if sku:
            product = (
                self.db.query(Product)
                .filter(
                    Product.organization_id == self.organization_id,
                    Product.sku.ilike(sku.strip()),
                )
                .one_or_none()
            )
            if product is None:
                return {"tool": "get_stockout_radar", "error": "product_not_found"}
            signal = build_product_signal(
                self.db,
                organization_id=self.organization_id,
                product=product,
            )
            radar = compute_stockout_risk(
                on_hand=signal.on_hand,
                avg_daily_movement=signal.avg_daily_movement,
                supplier_lead_time_days=signal.lead_time_days,
                safety_stock=signal.safety_stock,
            )
            return {
                "tool": "get_stockout_radar",
                "items": [
                    {
                        "sku": signal.sku,
                        "name": signal.name,
                        **radar,
                    }
                ],
            }
        signals = list_product_signals(
            self.db,
            organization_id=self.organization_id,
            only_actionable=False,
            limit=limit,
        )
        items = []
        for signal in signals:
            radar = compute_stockout_risk(
                on_hand=signal.on_hand,
                avg_daily_movement=signal.avg_daily_movement,
                supplier_lead_time_days=signal.lead_time_days,
                safety_stock=signal.safety_stock,
            )
            items.append({"sku": signal.sku, "name": signal.name, **radar})
        items.sort(key=lambda r: float(r["risk_score"]), reverse=True)
        return {"tool": "get_stockout_radar", "items": items[:limit]}

    def list_reorder_candidates(self, *, limit: int = 10) -> dict[str, Any]:
        signals = list_product_signals(
            self.db,
            organization_id=self.organization_id,
            only_actionable=True,
            lookback_days=LOOKBACK_DAYS_DEFAULT,
            limit=limit,
        )
        return {
            "tool": "list_reorder_candidates",
            "items": [
                {
                    "product_id": str(s.product_id),
                    "sku": s.sku,
                    "name": s.name,
                    "on_hand": str(s.on_hand),
                    "recommended_qty": str(s.recommended_qty),
                    "below_reorder_point": s.below_reorder_point,
                }
                for s in signals
            ],
        }

    def invoke(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in ALLOWED_TOOLS:
            return {"error": "tool_not_allowlisted", "tool": name}
        args = arguments or {}
        # Drop unknown keys; only pass known params per tool
        handlers: dict[str, ToolFn] = {
            "list_low_stock": lambda: self.list_low_stock(limit=int(args.get("limit", 15))),
            "get_product_stock": lambda: self.get_product_stock(
                sku=args.get("sku"),
                product_id=args.get("product_id"),
            ),
            "get_recent_movements": lambda: self.get_recent_movements(
                limit=int(args.get("limit", 10)),
                sku=args.get("sku"),
            ),
            "list_open_purchase_orders": lambda: self.list_open_purchase_orders(
                limit=int(args.get("limit", 10)),
            ),
            "get_stockout_radar": lambda: self.get_stockout_radar(
                sku=args.get("sku"),
                limit=int(args.get("limit", 10)),
            ),
            "list_reorder_candidates": lambda: self.list_reorder_candidates(
                limit=int(args.get("limit", 10)),
            ),
        }
        return handlers[name]()


def select_tools_for_question(question: str) -> list[tuple[str, dict[str, Any]]]:
    """Deterministic tool planner for DemoAIProvider (keyword allowlist routing)."""
    q = question.lower()
    calls: list[tuple[str, dict[str, Any]]] = []

    sku = None
    for token in question.replace(",", " ").split():
        if token.upper().startswith("SKU-"):
            sku = token.upper().rstrip("?.!")
            break

    if any(w in q for w in ("low stock", "below reorder", "out of stock", "stockout risk")):
        calls.append(("list_low_stock", {"limit": 10}))
    if any(w in q for w in ("reorder", "order more", "what should i order", "buy")):
        calls.append(("list_reorder_candidates", {"limit": 10}))
    if any(w in q for w in ("purchase order", "open po", "pending po", "pos")):
        calls.append(("list_open_purchase_orders", {"limit": 10}))
    if any(w in q for w in ("movement", "ledger", "recent activity", "dispatch")):
        calls.append(("get_recent_movements", {"limit": 10, **({"sku": sku} if sku else {})}))
    if any(w in q for w in ("radar", "risk", "coverage")):
        calls.append(("get_stockout_radar", {"limit": 8, **({"sku": sku} if sku else {})}))
    if sku or any(w in q for w in ("how many", "on hand", "balance", "stock for")):
        if sku:
            calls.append(("get_product_stock", {"sku": sku}))
        elif not calls:
            calls.append(("list_low_stock", {"limit": 5}))

    if not calls:
        calls.append(("list_low_stock", {"limit": 5}))
        calls.append(("list_open_purchase_orders", {"limit": 5}))

    # de-dupe by tool name preserving order
    seen: set[str] = set()
    unique: list[tuple[str, dict[str, Any]]] = []
    for name, args in calls:
        if name in seen:
            continue
        seen.add(name)
        unique.append((name, args))
    return unique[:4]
