"""Role-gated mutation helpers (Milestone 2)."""

from __future__ import annotations

from fastapi import status

from app.dependencies import AuthContext
from app.errors import http_error

# Catalog / purchasing mutations
CATALOG_ROLES = frozenset({"owner", "inventory_manager"})
# Receiving, counts, transfers, dispatch
OPS_ROLES = frozenset({"owner", "inventory_manager", "staff"})


def require_roles(auth: AuthContext, allowed: frozenset[str], *, action: str) -> None:
    if auth.role not in allowed:
        raise http_error(
            status.HTTP_403_FORBIDDEN,
            "forbidden_role",
            f"Role '{auth.role}' cannot {action}",
            {"role": auth.role, "allowed_roles": sorted(allowed)},
        )
