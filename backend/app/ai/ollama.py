"""Optional Ollama adapter — local open model only; falls back to DemoAIProvider."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from pydantic import ValidationError

from app.ai.demo import DemoAIProvider
from app.ai.provider import AIProvider
from app.schemas.ai import AIResultEnvelope


class OllamaAIProvider(AIProvider):
    """
    Calls local Ollama `/api/chat` when available.

    On connection failure or invalid JSON output, falls back to DemoAIProvider.
    Stockout Radar numeric scores remain deterministic (computed upstream / via demo).
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

    async def _chat_json(self, *, system: str, user: str) -> dict[str, Any] | None:
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                if response.status_code != 200:
                    return None
                body = response.json()
                content = body.get("message", {}).get("content") or body.get("response") or ""
                return _parse_json_object(content)
        except Exception:
            return None

    async def reorder_recommendations(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fallback = await self._fallback.reorder_recommendations(
            input_payload=input_payload,
            context_ids=context_ids,
            options=options,
        )
        if not await self._ping():
            fallback["result"]["provider"] = "demo-fallback"
            fallback["explanation"] += " Ollama unreachable; used DemoAIProvider."
            return fallback

        system = (
            "You are Inventory AI reorder assistant. Respond with JSON only matching "
            '{"explanation": string, "summary": string}. '
            "Do not invent stock numbers; use the provided recommendations. "
            "Never claim certainty. Never change stock."
        )
        user = json.dumps(
            {
                "recommendations": input_payload.get("recommendations", [])[:15],
                "task": "Explain the reorder recommendations briefly.",
            },
            default=str,
        )
        generated = await self._chat_json(system=system, user=user)
        if not generated:
            fallback["result"]["provider"] = "demo-fallback"
            fallback["explanation"] += " Ollama returned invalid output; used DemoAIProvider."
            return fallback

        explanation = str(generated.get("explanation") or generated.get("summary") or fallback["explanation"])
        fallback["explanation"] = explanation
        fallback["result"]["provider"] = "ollama"
        fallback["result"]["ollama_model"] = self.model
        fallback["requires_confirmation"] = True
        return _validate_envelope(fallback)

    async def inventory_question(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fallback = await self._fallback.inventory_question(
            input_payload=input_payload,
            context_ids=context_ids,
            options=options,
        )
        if not await self._ping():
            fallback["result"]["provider"] = "demo-fallback"
            return fallback

        system = (
            "You answer inventory questions using ONLY the provided tool_results JSON. "
            "Respond with JSON: {\"answer\": string, \"explanation\": string}. "
            "Label uncertainty; do not invent SKUs or quantities; no certainty claims."
        )
        user = json.dumps(
            {
                "question": input_payload.get("question"),
                "tool_results": fallback["result"].get("tool_results")
                or input_payload.get("tool_results")
                or [],
            },
            default=str,
        )
        generated = await self._chat_json(system=system, user=user)
        if not generated or "answer" not in generated:
            fallback["result"]["provider"] = "demo-fallback"
            return fallback

        fallback["result"]["answer"] = str(generated["answer"])
        fallback["result"]["provider"] = "ollama"
        fallback["result"]["ollama_model"] = self.model
        fallback["result"]["labeled_ai"] = True
        if generated.get("explanation"):
            fallback["explanation"] = str(generated["explanation"])
        return _validate_envelope(fallback)

    async def stockout_radar(
        self,
        *,
        input_payload: dict[str, Any],
        context_ids: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Numeric risk stays deterministic via Demo / upstream compute
        result = await self._fallback.stockout_radar(
            input_payload=input_payload,
            context_ids=context_ids,
            options=options,
        )
        if await self._ping():
            system = (
                "Explain Stockout Radar results briefly. JSON only: "
                '{"explanation": string}. Never claim a stockout will happen.'
            )
            user = json.dumps({"items": result["result"].get("items") or result["result"]}, default=str)
            generated = await self._chat_json(system=system, user=user)
            if generated and generated.get("explanation"):
                result["explanation"] = str(generated["explanation"])
                result["result"]["provider"] = "ollama"
                result["result"]["ollama_model"] = self.model
            else:
                result["result"]["provider"] = "demo-fallback"
        else:
            result["result"]["provider"] = "demo-fallback"
        return result


def _parse_json_object(content: str) -> dict[str, Any] | None:
    text = (content or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None


def _validate_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return AIResultEnvelope.model_validate(payload).model_dump()
    except ValidationError:
        # Keep original keys if validation fails on nested shapes
        return payload
