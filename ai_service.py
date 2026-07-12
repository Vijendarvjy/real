"""
AI layer, abstracted behind a base interface so the image/text vendor
can be swapped (OpenAI, Azure OpenAI, Stability, etc.) without touching
the Streamlit UI code.
"""

import os
import re
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DesignRequest:
    room_type: str
    length_ft: float
    width_ft: float
    height_ft: float
    style: str
    budget_tier: str
    selections: dict = field(default_factory=dict)  # field_key -> chosen option
    notes: str = ""


@dataclass
class DesignResult:
    summary: str
    layout_plan: str
    materials: list
    color_palette: list
    estimated_cost_range: str
    image_url: Optional[str] = None
    image_bytes: Optional[bytes] = None
    raw_text: str = ""
    error: Optional[str] = None


class AIDesignProvider(ABC):
    """Interface every AI vendor implementation must satisfy."""

    @abstractmethod
    def generate_recommendation(self, req: DesignRequest) -> DesignResult:
        ...

    @abstractmethod
    def generate_preview_image(self, req: DesignRequest, recommendation: DesignResult) -> DesignResult:
        ...


def _extract_json(text: str) -> Optional[dict]:
    """
    Pull the first well-formed JSON object out of a model response by
    walking brace depth, since models occasionally wrap JSON in prose
    or markdown fences. Falls back to None if nothing parses.
    """
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    return None


def _area_sqft(req: DesignRequest) -> float:
    return round(req.length_ft * req.width_ft, 1)


class OpenAIProvider(AIDesignProvider):
    """Uses OpenAI Chat Completions for the design brief and
    gpt-image-1 (falls back to DALL-E 3) for the preview render."""

    def __init__(self, api_key: Optional[str] = None,
                 text_model: str = "gpt-4o-mini",
                 image_model: str = "gpt-image-1"):
        from openai import OpenAI  # imported lazily so app still loads without the package configured
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")
        self.client = OpenAI(api_key=self.api_key)
        self.text_model = text_model
        self.image_model = image_model

    def _build_prompt(self, req: DesignRequest) -> str:
        selection_lines = "\n".join(f"- {k}: {v}" for k, v in req.selections.items())
        return f"""
You are a senior interior designer producing a design brief for a {req.room_type}
in an apartment. Room dimensions: {req.length_ft} ft x {req.width_ft} ft, ceiling
height {req.height_ft} ft (area ~{_area_sqft(req)} sq ft).

Design style: {req.style}
Budget tier: {req.budget_tier}
Client selections:
{selection_lines}
Additional notes: {req.notes or "None"}

Return ONLY a JSON object, no markdown fences, no preamble, with this exact shape:
{{
  "summary": "2-3 sentence overview of the design concept for this room",
  "layout_plan": "short paragraph describing furniture/fixture placement given the dimensions",
  "materials": ["material or finish recommendation", "..."],
  "color_palette": ["color name or hex-ish description", "..."],
  "estimated_cost_range": "a rough cost range in INR for this room at the given budget tier, e.g. '₹1.8L - ₹2.5L'",
  "image_prompt": "a single vivid, concrete prompt (no brand names, no people) describing this room's interior for an AI image generator, incorporating the style, materials, colors and approximate proportions"
}}
""".strip()

    def generate_recommendation(self, req: DesignRequest) -> DesignResult:
        try:
            response = self.client.chat.completions.create(
                model=self.text_model,
                messages=[{"role": "user", "content": self._build_prompt(req)}],
                temperature=0.7,
            )
            raw_text = response.choices[0].message.content or ""
        except Exception as exc:  # network/auth/rate-limit errors
            logger.exception("OpenAI text generation failed")
            return DesignResult(
                summary="", layout_plan="", materials=[], color_palette=[],
                estimated_cost_range="", raw_text="", error=str(exc),
            )

        data = _extract_json(raw_text)
        if data is None:
            # Regex fallback: try to salvage at least a summary line
            summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', raw_text)
            return DesignResult(
                summary=summary_match.group(1) if summary_match else raw_text[:300],
                layout_plan="", materials=[], color_palette=[],
                estimated_cost_range="", raw_text=raw_text,
                error="Could not fully parse AI response as JSON; showing best-effort text.",
            )

        result = DesignResult(
            summary=data.get("summary", ""),
            layout_plan=data.get("layout_plan", ""),
            materials=data.get("materials", []) or [],
            color_palette=data.get("color_palette", []) or [],
            estimated_cost_range=data.get("estimated_cost_range", ""),
            raw_text=raw_text,
        )
        # stash the image prompt for the next step without polluting the dataclass schema
        result.__dict__["_image_prompt"] = data.get("image_prompt", "")
        return result

    def generate_preview_image(self, req: DesignRequest, recommendation: DesignResult) -> DesignResult:
        prompt = recommendation.__dict__.get("_image_prompt") or (
            f"Interior photo of a {req.style} {req.room_type}, {_area_sqft(req)} sq ft, "
            f"realistic architectural visualization, no text, no people"
        )
        try:
            image = self.client.images.generate(
                model=self.image_model,
                prompt=prompt,
                size="1024x1024",
                n=1,
            )
            b64 = getattr(image.data[0], "b64_json", None)
            url = getattr(image.data[0], "url", None)
            if b64:
                import base64
                recommendation.image_bytes = base64.b64decode(b64)
            elif url:
                recommendation.image_url = url
        except Exception as exc:
            logger.exception("OpenAI image generation failed")
            recommendation.error = (recommendation.error or "") + f" | Image generation failed: {exc}"
        return recommendation


class StubProvider(AIDesignProvider):
    """No-network fallback so the UI is fully explorable without an API key."""

    def generate_recommendation(self, req: DesignRequest) -> DesignResult:
        return DesignResult(
            summary=f"[Demo mode] A {req.style.lower()} {req.room_type.lower()} concept "
                     f"tailored to your {_area_sqft(req)} sq ft space.",
            layout_plan="Add your OPENAI_API_KEY to generate a real, dimension-aware layout plan.",
            materials=[v for v in req.selections.values()][:4],
            color_palette=["Warm White", "Charcoal Grey", "Brass Accents"],
            estimated_cost_range="₹1.5L - ₹3L (placeholder)",
            raw_text="",
        )

    def generate_preview_image(self, req: DesignRequest, recommendation: DesignResult) -> DesignResult:
        recommendation.error = "Demo mode: no image generated. Add OPENAI_API_KEY for AI renders."
        return recommendation


def get_provider() -> AIDesignProvider:
    """Factory: returns a working OpenAI provider if a key is configured,
    otherwise falls back to the stub so the app never hard-crashes."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            return OpenAIProvider(api_key=api_key)
        except Exception:
            logger.exception("Falling back to StubProvider")
    return StubProvider()
