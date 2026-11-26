"""AIProvider interface — backend-only generative AI boundary."""

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Swappable AI backend. Calculations and stock balances stay in deterministic code."""

    @abstractmethod
    async def reorder_recommendations(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Recommend reorder quantities with explanation and sources."""

    @abstractmethod
    async def inventory_question(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Natural-language inventory Q&A over allowlisted read tools (stub)."""

    @abstractmethod
    async def stockout_radar(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Explain Stockout Radar risk signals (formula remains deterministic)."""
