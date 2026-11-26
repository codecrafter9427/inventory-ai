"""Milestone 3 — DemoAIProvider, Stockout Radar determinism, AI endpoint auth."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.ai.demo import DemoAIProvider
from app.services.stockout_radar import FORMULA, compute_stockout_risk


def test_stockout_radar_formula_deterministic() -> None:
    a = compute_stockout_risk(
        on_hand=10,
        avg_daily_movement=2,
        supplier_lead_time_days=7,
        safety_stock=5,
    )
    b = compute_stockout_risk(
        on_hand=10,
        avg_daily_movement=2,
        supplier_lead_time_days=7,
        safety_stock=5,
    )
    assert a == b
    assert a["formula"] == FORMULA
    # coverage=5; buffer=7+2.5=9.5; risk=1-5/9.5≈0.474
    assert a["risk_score"] == round(1.0 - (5.0 / 9.5), 3)
    assert a["risk_level"] in {"low", "medium", "high"}
    assert a["inputs"]["coverage_days"] == 5.0
    assert any("not a prediction" in s.lower() or "risk signal" in s.lower() for s in a["assumptions"])


def test_stockout_radar_zero_movement_fallback() -> None:
    with_stock = compute_stockout_risk(
        on_hand=12,
        avg_daily_movement=0,
        supplier_lead_time_days=7,
        safety_stock=3,
    )
    without = compute_stockout_risk(
        on_hand=0,
        avg_daily_movement=0,
        supplier_lead_time_days=7,
        safety_stock=3,
    )
    assert with_stock["risk_score"] == 0.0
    assert without["risk_score"] == 1.0


def test_demo_ai_provider_stockout_and_reorder() -> None:
    provider = DemoAIProvider()

    async def _run() -> None:
        radar = await provider.stockout_radar(
            input_payload={
                "product_id": "p1",
                "on_hand": 10,
                "avg_daily_movement": 2,
                "supplier_lead_time_days": 7,
                "safety_stock": 5,
            }
        )
        assert radar["result"]["provider"] == "demo"
        assert radar["result"]["risk_score"] == compute_stockout_risk(
            on_hand=10,
            avg_daily_movement=2,
            supplier_lead_time_days=7,
            safety_stock=5,
        )["risk_score"]
        assert radar["requires_confirmation"] is False

        reorder = await provider.reorder_recommendations(
            input_payload={
                "recommendations": [
                    {
                        "product_id": "p1",
                        "sku": "SKU-001",
                        "recommended_qty": "12",
                        "assumptions": ["demo"],
                    }
                ]
            }
        )
        assert reorder["requires_confirmation"] is True
        assert reorder["result"]["provider"] == "demo"
        assert reorder["result"]["recommendations"][0]["sku"] == "SKU-001"

        qa = await provider.inventory_question(
            input_payload={
                "question": "Which products are low stock?",
                "tool_results": [
                    {
                        "tool": "list_low_stock",
                        "items": [{"sku": "SKU-009", "on_hand": "2", "product_id": "x"}],
                        "count": 1,
                    }
                ],
            }
        )
        assert qa["result"]["provider"] == "demo"
        assert "SKU-009" in qa["result"]["answer"]
        assert qa["result"]["labeled_ai"] is True

    asyncio.run(_run())


def test_ai_endpoints_require_auth(client: TestClient) -> None:
    for path, body in (
        ("/api/v1/ai/reorder-recommendations", {}),
        ("/api/v1/ai/inventory-question", {"question": "low stock?"}),
        ("/api/v1/ai/stockout-radar", {}),
        ("/api/v1/ai/confirm-draft-po", {"confirm": True, "lines": []}),
    ):
        res = client.post(path, json=body)
        assert res.status_code == 401, path
        assert res.json()["error"]["code"] == "unauthorized"


def test_stockout_radar_endpoint_manual_inputs(client: TestClient, admin_token: str) -> None:
    res = client.post(
        "/api/v1/ai/stockout-radar",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "on_hand": 10,
            "avg_daily_movement": 2,
            "supplier_lead_time_days": 7,
            "safety_stock": 5,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["result"]["formula"] == FORMULA
    item = body["result"]["items"][0]
    expected = compute_stockout_risk(
        on_hand=10,
        avg_daily_movement=2,
        supplier_lead_time_days=7,
        safety_stock=5,
    )
    assert item["risk_score"] == expected["risk_score"]
    assert "certainty" not in body["explanation"].lower() or "not" in body["explanation"].lower()


def test_reorder_recommendations_authenticated(client: TestClient, admin_token: str) -> None:
    res = client.post(
        "/api/v1/ai/reorder-recommendations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"only_actionable": True, "lookback_days": 30, "limit": 25},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["requires_confirmation"] is True
    assert "recommendations" in body["result"]
    assert body["result"].get("labeled_ai") is True


def test_inventory_question_uses_tools(client: TestClient, admin_token: str) -> None:
    res = client.post(
        "/api/v1/ai/inventory-question",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"question": "Which products are low stock?"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["result"]["labeled_ai"] is True
    assert "list_low_stock" in body["result"]["tools_used"]
    assert body["result"]["answer"]


def test_confirm_draft_po_requires_confirm_flag(client: TestClient, admin_token: str) -> None:
    # First get a recommendation if any
    rec = client.post(
        "/api/v1/ai/reorder-recommendations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"only_actionable": False, "limit": 5},
    )
    assert rec.status_code == 200
    recommendations = rec.json()["result"]["recommendations"]
    if not recommendations:
        pytest.skip("No products available for draft PO line")
    line = recommendations[0]
    qty = line["recommended_qty"] if float(line["recommended_qty"]) > 0 else "1"

    denied = client.post(
        "/api/v1/ai/confirm-draft-po",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "confirm": False,
            "lines": [{"product_id": line["product_id"], "quantity": qty}],
        },
    )
    assert denied.status_code == 400
    assert denied.json()["error"]["code"] == "confirmation_required"

    created = client.post(
        "/api/v1/ai/confirm-draft-po",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "confirm": True,
            "lines": [{"product_id": line["product_id"], "quantity": qty}],
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["result"]["status"] == "draft"
    assert body["result"]["stock_changed"] is False
    assert body["result"]["po_number"]


def test_confirm_draft_po_forbidden_for_staff(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "staff@demo.inventory.local", "password": "demo-password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    res = client.post(
        "/api/v1/ai/confirm-draft-po",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "confirm": True,
            "lines": [{"product_id": "00000000-0000-0000-0000-000000000001", "quantity": "1"}],
        },
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "forbidden_role"
