"""m6_org_reorder_defaults

Revision ID: b7c1d2e3f4a5
Revises: 6a84411e515c
Create Date: 2026-11-27 23:55:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c1d2e3f4a5"
down_revision: Union[str, None] = "6a84411e515c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column(
            "default_reorder_point",
            sa.Numeric(14, 4),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "default_safety_stock",
            sa.Numeric(14, 4),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "default_lead_time_days",
            sa.Integer(),
            nullable=False,
            server_default="7",
        ),
    )


def downgrade() -> None:
    op.drop_column("organizations", "default_lead_time_days")
    op.drop_column("organizations", "default_safety_stock")
    op.drop_column("organizations", "default_reorder_point")
