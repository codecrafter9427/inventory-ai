"""
Seed Inventory AI with fictional demo data (Milestone 1).

Minimums: 30 products, 3 locations, 5 suppliers, 8 POs, movement history.
Also seeds a second organization for tenant isolation tests.

Usage (from backend/ with venv active and DB up):
  python seed.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import SessionLocal, engine
from app.models import (
    AuditEvent,
    Category,
    Location,
    Organization,
    Product,
    PurchaseOrder,
    PurchaseOrderLine,
    Role,
    StockBalance,
    StockCount,
    StockCountLine,
    StockMovement,
    StockTransfer,
    StockTransferLine,
    Supplier,
    Unit,
    User,
)
from app.security import hash_password

DEMO_PASSWORD = "demo-password"

PRODUCT_NAMES = [
    ("SKU-001", "Aurora LED Desk Lamp", "Lighting", "12.50", "24.99", "10"),
    ("SKU-002", "Nimbus Wireless Mouse", "Peripherals", "8.20", "19.99", "15"),
    ("SKU-003", "Cascade USB-C Hub", "Peripherals", "18.00", "39.99", "8"),
    ("SKU-004", "Summit Notebook A5", "Stationery", "2.10", "6.50", "40"),
    ("SKU-005", "Harbor Ballpoint Pack", "Stationery", "1.40", "4.25", "50"),
    ("SKU-006", "Cedar Desk Organizer", "Office", "6.75", "16.00", "12"),
    ("SKU-007", "Pulse HDMI Cable 2m", "Cables", "3.20", "9.99", "25"),
    ("SKU-008", "Orbit Bluetooth Speaker", "Audio", "14.00", "34.99", "10"),
    ("SKU-009", "Lumen Monitor Stand", "Office", "22.00", "49.00", "6"),
    ("SKU-010", "Drift Ergonomic Cushion", "Office", "11.50", "28.00", "10"),
    ("SKU-011", "Pixel Screen Cleaner", "Accessories", "1.80", "5.99", "30"),
    ("SKU-012", "Forge Tool Kit Mini", "Tools", "16.40", "39.50", "8"),
    ("SKU-013", "River Water Bottle 750ml", "Lifestyle", "4.50", "14.00", "20"),
    ("SKU-014", "Grove Plant Pot Set", "Lifestyle", "7.25", "18.50", "12"),
    ("SKU-015", "Atlas Wall Calendar", "Stationery", "3.00", "9.50", "18"),
    ("SKU-016", "Beacon Night Light", "Lighting", "5.60", "14.99", "15"),
    ("SKU-017", "Quill Gel Pen Set", "Stationery", "2.80", "7.99", "35"),
    ("SKU-018", "Copper Cable Ties 100pk", "Cables", "1.10", "3.99", "40"),
    ("SKU-019", "Nova Webcam Cover", "Accessories", "0.90", "2.99", "50"),
    ("SKU-020", "Stride Standing Mat", "Office", "28.00", "69.00", "5"),
    ("SKU-021", "Echo Headset Lite", "Audio", "19.50", "45.00", "10"),
    ("SKU-022", "Prism Sticky Notes", "Stationery", "1.20", "3.50", "45"),
    ("SKU-023", "Vertex Laptop Sleeve", "Accessories", "9.80", "24.00", "14"),
    ("SKU-024", "Amber Desk Clock", "Office", "8.40", "21.00", "10"),
    ("SKU-025", "Cliff Power Bank 10k", "Electronics", "15.00", "36.00", "12"),
    ("SKU-026", "Meadow Tea Infuser", "Lifestyle", "3.60", "9.99", "20"),
    ("SKU-027", "Bolt Extension Cord", "Cables", "6.10", "15.50", "16"),
    ("SKU-028", "Shade Monitor Hood", "Accessories", "10.20", "26.00", "8"),
    ("SKU-029", "Canvas Tote Branded", "Lifestyle", "4.00", "12.00", "25"),
    ("SKU-030", "Iron Stapler Heavy", "Office", "5.50", "13.99", "15"),
]


def _utc(days_ago: int = 0, hours: int = 12) -> datetime:
    base = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return base.replace(hour=hours % 24, minute=0, second=0, microsecond=0)


def _clear_all(db: Session) -> None:
    """Idempotent reseed: wipe inventory tables (order matters for FKs)."""
    for model in (
        AuditEvent,
        StockTransferLine,
        StockTransfer,
        StockCountLine,
        StockCount,
        StockMovement,
        StockBalance,
        PurchaseOrderLine,
        PurchaseOrder,
        Product,
        Category,
        Unit,
        Location,
        Supplier,
        User,
        Role,
        Organization,
    ):
        db.execute(delete(model))
    db.commit()


def _seed_org(
    db: Session,
    *,
    name: str,
    slug: str,
    full_catalog: bool,
) -> tuple[Organization, dict[str, User]]:
    org = Organization(name=name, slug=slug)
    db.add(org)
    db.flush()

    role_defs = [
        ("owner", "Owner / Admin", "Settings, users, all reports"),
        ("inventory_manager", "Inventory Manager", "Catalog, suppliers, purchasing, stock"),
        ("staff", "Staff", "Receiving, counts, transfers, dispatch"),
    ]
    roles: dict[str, Role] = {}
    for code, role_name, description in role_defs:
        role = Role(
            organization_id=org.id,
            code=code,
            name=role_name,
            description=description,
        )
        db.add(role)
        roles[code] = role
    db.flush()

    password_hash = hash_password(DEMO_PASSWORD)
    users: dict[str, User] = {}

    if full_catalog:
        user_specs = [
            ("admin@demo.inventory.local", "Demo Owner", "owner"),
            ("manager@demo.inventory.local", "Demo Manager", "inventory_manager"),
            ("staff@demo.inventory.local", "Demo Staff", "staff"),
        ]
    else:
        user_specs = [
            ("other@demo.inventory.local", "Other Org Admin", "owner"),
        ]

    for email, display_name, role_code in user_specs:
        user = User(
            organization_id=org.id,
            role_id=roles[role_code].id,
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            is_active=True,
        )
        db.add(user)
        users[role_code if full_catalog else "owner"] = user
    db.flush()

    if not full_catalog:
        # Minimal second-org footprint for tenant tests only
        unit = Unit(organization_id=org.id, code="ea", name="Each")
        db.add(unit)
        db.flush()
        db.add(
            Product(
                organization_id=org.id,
                sku="OTHER-001",
                name="Other Org Widget",
                unit_id=unit.id,
                cost=Decimal("1.00"),
                selling_price=Decimal("2.00"),
                reorder_point=Decimal("1"),
                safety_stock=Decimal("1"),
                lead_time_days=5,
                is_active=True,
            )
        )
        db.flush()
        return org, users

    categories = {}
    for cat_name in sorted({p[2] for p in PRODUCT_NAMES}):
        cat = Category(organization_id=org.id, name=cat_name, description=f"{cat_name} products")
        db.add(cat)
        categories[cat_name] = cat

    units = {
        "ea": Unit(organization_id=org.id, code="ea", name="Each"),
        "pk": Unit(organization_id=org.id, code="pk", name="Pack"),
        "bx": Unit(organization_id=org.id, code="bx", name="Box"),
    }
    for unit in units.values():
        db.add(unit)
    db.flush()

    locations = [
        Location(
            organization_id=org.id,
            code="WH-MAIN",
            name="Main Warehouse",
            address="100 Demo Industrial Way, Faketown",
            bin_shelf_notes="Aisle A–D",
        ),
        Location(
            organization_id=org.id,
            code="WH-EAST",
            name="East Satellite",
            address="22 Harbor Road, Faketown",
            bin_shelf_notes="Bins E1–E8",
        ),
        Location(
            organization_id=org.id,
            code="STORE-01",
            name="Retail Floor Stock",
            address="5 Market Street, Faketown",
            bin_shelf_notes="Backroom shelves",
        ),
    ]
    db.add_all(locations)
    db.flush()

    suppliers = [
        Supplier(
            organization_id=org.id,
            name="Northwind Supplies Co",
            email="orders@northwind.example",
            phone="+1-555-0101",
            lead_time_days=5,
        ),
        Supplier(
            organization_id=org.id,
            name="Blue Harbor Distributors",
            email="sales@blueharbor.example",
            phone="+1-555-0102",
            lead_time_days=7,
        ),
        Supplier(
            organization_id=org.id,
            name="Cedar Peak Wholesale",
            email="desk@cedarpeak.example",
            phone="+1-555-0103",
            lead_time_days=10,
        ),
        Supplier(
            organization_id=org.id,
            name="Orbit Office Trading",
            email="hello@orbitoffice.example",
            phone="+1-555-0104",
            lead_time_days=4,
        ),
        Supplier(
            organization_id=org.id,
            name="Lumen Industrial Parts",
            email="parts@lumenind.example",
            phone="+1-555-0105",
            lead_time_days=12,
        ),
    ]
    db.add_all(suppliers)
    db.flush()

    products: list[Product] = []
    for idx, (sku, pname, cat_name, cost, price, reorder) in enumerate(PRODUCT_NAMES):
        unit_code = "pk" if "Pack" in pname or "Set" in pname else "ea"
        if "Cable Ties" in pname:
            unit_code = "bx"
        product = Product(
            organization_id=org.id,
            sku=sku,
            name=pname,
            description=f"Fictional demo product: {pname}",
            barcode=f"8901000{idx + 1:05d}",
            category_id=categories[cat_name].id,
            unit_id=units[unit_code].id,
            cost=Decimal(cost),
            selling_price=Decimal(price),
            reorder_point=Decimal(reorder),
            safety_stock=Decimal(reorder) / Decimal("2"),
            lead_time_days=5 + (idx % 8),
            is_active=True,
        )
        db.add(product)
        products.append(product)
    db.flush()

    owner = users["owner"]
    manager = users["inventory_manager"]

    # Opening balances + movements at main warehouse
    for idx, product in enumerate(products):
        opening_qty = Decimal(20 + (idx % 15) * 3)
        main = locations[0]
        east = locations[1]
        store = locations[2]

        bal_main = StockBalance(
            organization_id=org.id,
            product_id=product.id,
            location_id=main.id,
            quantity=opening_qty,
        )
        db.add(bal_main)
        db.add(
            StockMovement(
                organization_id=org.id,
                product_id=product.id,
                location_id=main.id,
                movement_type="opening",
                quantity=opening_qty,
                balance_after=opening_qty,
                reason="Opening balance (seed)",
                actor_user_id=owner.id,
                created_at=_utc(60 - (idx % 10)),
            )
        )

        if idx % 3 == 0:
            east_qty = Decimal(5 + (idx % 7))
            db.add(
                StockBalance(
                    organization_id=org.id,
                    product_id=product.id,
                    location_id=east.id,
                    quantity=east_qty,
                )
            )
            db.add(
                StockMovement(
                    organization_id=org.id,
                    product_id=product.id,
                    location_id=east.id,
                    movement_type="opening",
                    quantity=east_qty,
                    balance_after=east_qty,
                    reason="Opening balance East (seed)",
                    actor_user_id=manager.id,
                    created_at=_utc(55),
                )
            )
        if idx % 4 == 0:
            store_qty = Decimal(3 + (idx % 5))
            db.add(
                StockBalance(
                    organization_id=org.id,
                    product_id=product.id,
                    location_id=store.id,
                    quantity=store_qty,
                )
            )
            db.add(
                StockMovement(
                    organization_id=org.id,
                    product_id=product.id,
                    location_id=store.id,
                    movement_type="opening",
                    quantity=store_qty,
                    balance_after=store_qty,
                    reason="Opening balance Store (seed)",
                    actor_user_id=manager.id,
                    created_at=_utc(50),
                )
            )

    db.flush()

    po_statuses = [
        "received",
        "received",
        "partially_received",
        "ordered",
        "ordered",
        "draft",
        "received",
        "cancelled",
    ]
    for i, status in enumerate(po_statuses):
        supplier = suppliers[i % len(suppliers)]
        location = locations[i % len(locations)]
        po = PurchaseOrder(
            organization_id=org.id,
            supplier_id=supplier.id,
            location_id=location.id,
            po_number=f"PO-2026-{i + 1:03d}",
            status=status,
            ordered_at=_utc(40 - i * 3) if status != "draft" else None,
            expected_at=_utc(20 - i * 2) if status not in {"draft", "cancelled"} else None,
            notes=f"Seed purchase order {i + 1}",
            created_by_id=manager.id,
        )
        db.add(po)
        db.flush()

        line_products = products[i * 3 : i * 3 + 3] or products[:3]
        for j, product in enumerate(line_products):
            qty_ordered = Decimal(10 + j * 5 + i)
            if status == "received":
                qty_received = qty_ordered
            elif status == "partially_received":
                qty_received = qty_ordered / Decimal("2")
            else:
                qty_received = Decimal("0")
            db.add(
                PurchaseOrderLine(
                    purchase_order_id=po.id,
                    product_id=product.id,
                    quantity_ordered=qty_ordered,
                    quantity_received=qty_received,
                    unit_cost=product.cost,
                )
            )

            if qty_received > 0:
                bal = db.execute(
                    select(StockBalance).where(
                        StockBalance.organization_id == org.id,
                        StockBalance.product_id == product.id,
                        StockBalance.location_id == location.id,
                    )
                ).scalar_one_or_none()
                if bal is None:
                    bal = StockBalance(
                        organization_id=org.id,
                        product_id=product.id,
                        location_id=location.id,
                        quantity=Decimal("0"),
                    )
                    db.add(bal)
                    db.flush()
                bal.quantity = bal.quantity + qty_received
                db.add(
                    StockMovement(
                        organization_id=org.id,
                        product_id=product.id,
                        location_id=location.id,
                        movement_type="receive",
                        quantity=qty_received,
                        balance_after=bal.quantity,
                        reference_type="purchase_order",
                        reference_id=po.id,
                        reason=f"Received against {po.po_number}",
                        actor_user_id=users["staff"].id,
                        created_at=_utc(30 - i),
                    )
                )

        # Sample dispatch / adjustment history on first few POs
        if i < 4:
            product = products[i]
            bal = db.execute(
                select(StockBalance).where(
                    StockBalance.organization_id == org.id,
                    StockBalance.product_id == product.id,
                    StockBalance.location_id == locations[0].id,
                )
            ).scalar_one()
            dispatch_qty = Decimal("2")
            if bal.quantity >= dispatch_qty:
                bal.quantity -= dispatch_qty
                db.add(
                    StockMovement(
                        organization_id=org.id,
                        product_id=product.id,
                        location_id=locations[0].id,
                        movement_type="dispatch",
                        quantity=-dispatch_qty,
                        balance_after=bal.quantity,
                        reason="Seed dispatch / demo sale",
                        actor_user_id=users["staff"].id,
                        created_at=_utc(15 - i),
                    )
                )

    db.add(
        AuditEvent(
            organization_id=org.id,
            actor_user_id=owner.id,
            action="seed.completed",
            entity_type="organization",
            entity_id=org.id,
            message="Demo seed completed",
            details={"products": len(products), "purchase_orders": 8},
        )
    )
    db.flush()
    return org, users


def seed(db: Session) -> None:
    settings = get_settings()
    _ = settings  # ensure env loaded
    _clear_all(db)
    primary, _ = _seed_org(
        db,
        name="Demo Retail Co",
        slug="demo-retail",
        full_catalog=True,
    )
    secondary, _ = _seed_org(
        db,
        name="Other Demo Org",
        slug="other-demo",
        full_catalog=False,
    )
    db.commit()
    print("Seed complete.")
    print(f"  Primary org: {primary.name} ({primary.id})")
    print(f"  Secondary org (tenant tests): {secondary.name} ({secondary.id})")
    print("Demo credentials (password for all: demo-password):")
    print("  Owner/Admin:       admin@demo.inventory.local")
    print("  Inventory Manager: manager@demo.inventory.local")
    print("  Staff:             staff@demo.inventory.local")
    print("  Other org owner:   other@demo.inventory.local")


def main() -> None:
    # Touch engine so connection errors surface clearly
    with engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
    db = SessionLocal()
    try:
        seed(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
