"""Product catalog CRUD — organization-scoped."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies import AuthContext, get_auth_context
from app.errors import http_error
from app.models import Category, Product, Unit
from app.permissions import CATALOG_ROLES, require_roles
from app.schemas.pagination import Page
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def _to_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        organization_id=product.organization_id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        barcode=product.barcode,
        category_id=product.category_id,
        unit_id=product.unit_id,
        cost=product.cost,
        selling_price=product.selling_price,
        reorder_point=product.reorder_point,
        safety_stock=product.safety_stock,
        lead_time_days=product.lead_time_days,
        is_active=product.is_active,
        archived_at=product.archived_at,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category_name=product.category.name if product.category else None,
        unit_code=product.unit.code if product.unit else None,
    )


def _get_org_product(db: Session, auth: AuthContext, product_id: uuid.UUID) -> Product:
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.unit))
        .filter(
            Product.id == product_id,
            Product.organization_id == auth.organization_id,
        )
        .one_or_none()
    )
    if product is None or product.archived_at is not None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Product not found")
    return product


@router.get("", response_model=Page[ProductResponse])
async def list_products(
    q: str | None = Query(default=None, description="Search SKU, name, or barcode"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    active_only: bool = Query(default=True),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Page[ProductResponse]:
    query = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.unit))
        .filter(
            Product.organization_id == auth.organization_id,
            Product.archived_at.is_(None),
        )
    )
    if active_only:
        query = query.filter(Product.is_active.is_(True))
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Product.sku.ilike(term),
                Product.name.ilike(term),
                Product.barcode.ilike(term),
            )
        )

    total = query.count()
    rows = (
        query.order_by(Product.sku.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return Page(
        items=[_to_response(p) for p in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ProductResponse:
    require_roles(auth, CATALOG_ROLES, action="create products")

    unit = (
        db.query(Unit)
        .filter(Unit.id == body.unit_id, Unit.organization_id == auth.organization_id)
        .one_or_none()
    )
    if unit is None:
        raise http_error(status.HTTP_400_BAD_REQUEST, "invalid_unit", "Unit not found in organization")

    if body.category_id is not None:
        category = (
            db.query(Category)
            .filter(
                Category.id == body.category_id,
                Category.organization_id == auth.organization_id,
                Category.archived_at.is_(None),
            )
            .one_or_none()
        )
        if category is None:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                "invalid_category",
                "Category not found in organization",
            )

    barcode = body.barcode.strip() if body.barcode else None
    if barcode == "":
        barcode = None

    product = Product(
        organization_id=auth.organization_id,
        sku=body.sku.strip(),
        name=body.name.strip(),
        description=body.description,
        barcode=barcode,
        category_id=body.category_id,
        unit_id=body.unit_id,
        cost=body.cost,
        selling_price=body.selling_price,
        reorder_point=body.reorder_point,
        safety_stock=body.safety_stock,
        lead_time_days=body.lead_time_days,
        is_active=body.is_active,
    )
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise http_error(
            status.HTTP_409_CONFLICT,
            "duplicate_product",
            "SKU or barcode already exists in this organization",
        ) from None

    db.refresh(product)
    product = _get_org_product(db, auth, product.id)
    return _to_response(product)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ProductResponse:
    return _to_response(_get_org_product(db, auth, product_id))


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ProductResponse:
    require_roles(auth, CATALOG_ROLES, action="update products")
    product = _get_org_product(db, auth, product_id)
    data = body.model_dump(exclude_unset=True)

    if "unit_id" in data and data["unit_id"] is not None:
        unit = (
            db.query(Unit)
            .filter(Unit.id == data["unit_id"], Unit.organization_id == auth.organization_id)
            .one_or_none()
        )
        if unit is None:
            raise http_error(status.HTTP_400_BAD_REQUEST, "invalid_unit", "Unit not found in organization")

    if "category_id" in data and data["category_id"] is not None:
        category = (
            db.query(Category)
            .filter(
                Category.id == data["category_id"],
                Category.organization_id == auth.organization_id,
                Category.archived_at.is_(None),
            )
            .one_or_none()
        )
        if category is None:
            raise http_error(
                status.HTTP_400_BAD_REQUEST,
                "invalid_category",
                "Category not found in organization",
            )

    if "sku" in data and data["sku"] is not None:
        data["sku"] = data["sku"].strip()
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    if "barcode" in data:
        barcode = data["barcode"].strip() if data["barcode"] else None
        data["barcode"] = barcode or None

    for key, value in data.items():
        setattr(product, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise http_error(
            status.HTTP_409_CONFLICT,
            "duplicate_product",
            "SKU or barcode already exists in this organization",
        ) from None

    product = _get_org_product(db, auth, product_id)
    return _to_response(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_product(
    product_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> None:
    require_roles(auth, CATALOG_ROLES, action="archive products")
    product = _get_org_product(db, auth, product_id)
    product.archived_at = datetime.now(timezone.utc)
    product.is_active = False
    db.commit()
