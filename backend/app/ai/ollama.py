"""Optional Ollama adapter stub — not fully wired; falls back to DemoAIProvider behavior."""

from typing import Any

import httpx

from app.ai.demo import DemoAIProvider
from app.ai.provider import AIProvider


class OllamaAIProvider(AIProvider):
    """
    Skeleton adapter for local Ollama.

    Real prompt wiring and schema validation are Coming Soon.
    On connection failure, responses fall back to DemoAIProvider.
    """

    def __init__(self, *, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._fallback = DemoAIProvider()

    async def _ping(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def reorder_recommendations(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Stub: no real generation yet — mark provider and use demo payload
        result = await self._fallback.reorder_recommendations(
            input_payload=input_payload,
            context_ids=context_ids,
            options=options,
        )
        available = await self._ping()
        result["result"]["provider"] = "ollama-stub" if available else "demo-fallback"
        result["explanation"] += (
            " Ollama adapter stub only; full local model wiring is Coming Soon."
            if available
            else " Ollama unreachable; used DemoAIProvider fallback."
        )
        return result

    async def inventory_question(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = await self._fallback.inventory_question(
            input_payload=input_payload,
            context_ids=context_ids,
            options=options,
        )
        available = await self._ping()
        result["result"]["provider"] = "ollama-stub" if available else "demo-fallback"
        return result

    async def stockout_radar(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Risk score stays deterministic via demo formula path
        return await self._fallback.stockout_radar(
            input_payload=input_payload,
            context_ids=context_ids,
            options=options,
        )
