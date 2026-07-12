"""
AI Apartment Interior Designer — single-file Streamlit app.

Select and customize interior designs (bedrooms, hall, kitchen, doors,
windows, TV unit, bathroom) based on real room dimensions, with
AI-generated recommendations and preview render images (OpenAI GPT +
gpt-image-2 / GPT-Image models). Everything lives in this one file on purpose —
avoids any multi-file import path issues on Streamlit Cloud.

Setup:
    pip install -r requirements.txt
    export OPENAI_API_KEY="sk-..."   (optional — runs in demo mode without it)
    streamlit run app.py
"""

import os
import re
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import streamlit as st

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Apartment Designer",
    page_icon="🏢",
    layout="wide",
)

# ============================================================
# CONFIG (room types, styles, budget tiers)
# ============================================================

# Each room has: icon, default (L x W x H) in feet, and a list of
# customization fields. Each field is (key, label, type, options/range)
ROOM_CONFIG = {
    "Master Bedroom": {
        "icon": "🛏️",
        "default_dims": {"length": 14.0, "width": 12.0, "height": 10.0},
        "fields": {
            "bed_size": {
                "label": "Bed Size",
                "options": ["Queen", "King", "California King", "Double"],
            },
            "wardrobe_type": {
                "label": "Wardrobe Type",
                "options": ["Sliding Door", "Hinged Door", "Walk-in Closet", "Open Wardrobe"],
            },
            "flooring": {
                "label": "Flooring",
                "options": ["Engineered Wood", "Laminate", "Vitrified Tile", "Carpet"],
            },
            "wall_finish": {
                "label": "Wall Finish",
                "options": ["Textured Paint", "Wallpaper (Accent Wall)", "Wood Paneling", "Plain Matte Paint"],
            },
            "lighting": {
                "label": "Lighting",
                "options": ["Cove Lighting", "Pendant Lights", "Recessed Spotlights", "Chandelier"],
            },
        },
    },
    "Kids Bedroom": {
        "icon": "🧸",
        "default_dims": {"length": 11.0, "width": 10.0, "height": 10.0},
        "fields": {
            "bed_size": {
                "label": "Bed Size",
                "options": ["Single", "Bunk Bed", "Trundle Bed", "Twin"],
            },
            "study_zone": {
                "label": "Study Zone",
                "options": ["Wall-mounted Desk", "Corner Study Table", "None"],
            },
            "flooring": {
                "label": "Flooring",
                "options": ["Vinyl (Soft)", "Laminate", "Carpet Tiles"],
            },
            "theme": {
                "label": "Theme",
                "options": ["Space", "Jungle Safari", "Pastel Minimal", "Sports"],
            },
        },
    },
    "Living / Hall": {
        "icon": "🛋️",
        "default_dims": {"length": 20.0, "width": 15.0, "height": 10.0},
        "fields": {
            "seating_layout": {
                "label": "Seating Layout",
                "options": ["L-Shaped Sofa", "Straight Sofa + Chairs", "U-Shaped Sofa", "Modular Sectional"],
            },
            "tv_unit_style": {
                "label": "TV Unit Style",
                "options": ["Floating Wall-mounted", "Console with Storage", "Entertainment Wall Panel", "Corner Unit"],
            },
            "false_ceiling": {
                "label": "False Ceiling",
                "options": ["Full Gypsum Ceiling", "Perimeter Cove Ceiling", "None"],
            },
            "flooring": {
                "label": "Flooring",
                "options": ["Italian Marble", "Vitrified Tile (Large Format)", "Engineered Wood"],
            },
            "color_palette": {
                "label": "Color Palette",
                "options": ["Warm Neutrals", "Cool Greys", "Earthy Tones", "Monochrome + Accent"],
            },
        },
    },
    "Kitchen": {
        "icon": "🍳",
        "default_dims": {"length": 12.0, "width": 9.0, "height": 9.5},
        "fields": {
            "layout": {
                "label": "Kitchen Layout",
                "options": ["L-Shaped", "Parallel / Galley", "U-Shaped", "Island"],
            },
            "countertop": {
                "label": "Countertop Material",
                "options": ["Granite", "Quartz", "Marble", "Concrete"],
            },
            "cabinet_finish": {
                "label": "Cabinet Finish",
                "options": ["High-Gloss Acrylic", "Matte Laminate", "Wood Veneer", "PU Paint"],
            },
            "backsplash": {
                "label": "Backsplash",
                "options": ["Ceramic Tile", "Glass Panel", "Natural Stone"],
            },
        },
    },
    "Doors": {
        "icon": "🚪",
        "default_dims": {"length": 3.0, "width": 0.2, "height": 7.0},
        "fields": {
            "door_type": {
                "label": "Door Type",
                "options": ["Flush Door", "Panel Door", "Sliding Glass Door", "French Door"],
            },
            "material": {
                "label": "Material",
                "options": ["Engineered Wood", "Solid Wood (Teak)", "UPVC", "Aluminium + Glass"],
            },
            "finish": {
                "label": "Finish",
                "options": ["Laminate", "Veneer + Polish", "Paint Finish"],
            },
        },
    },
    "Windows": {
        "icon": "🪟",
        "default_dims": {"length": 4.0, "width": 0.2, "height": 4.5},
        "fields": {
            "window_type": {
                "label": "Window Type",
                "options": ["Sliding", "Casement", "Fixed + Openable Combo", "Bay Window"],
            },
            "frame_material": {
                "label": "Frame Material",
                "options": ["UPVC", "Aluminium", "Wood"],
            },
            "glass_type": {
                "label": "Glass Type",
                "options": ["Clear Glass", "Tinted Glass", "Double Glazed (Insulated)", "Frosted"],
            },
            "treatment": {
                "label": "Window Treatment",
                "options": ["Roller Blinds", "Sheer Curtains", "Wooden Venetian Blinds", "None"],
            },
        },
    },
    "TV / Media Unit": {
        "icon": "📺",
        "default_dims": {"length": 8.0, "width": 1.5, "height": 6.0},
        "fields": {
            "unit_style": {
                "label": "Unit Style",
                "options": ["Wall-mounted Floating Panel", "Low Console Unit", "Wall-to-Wall Storage Wall"],
            },
            "material": {
                "label": "Material",
                "options": ["Wood Veneer + Laminate", "High-Gloss PU", "Matte Laminate + Stone Cladding"],
            },
            "backdrop": {
                "label": "TV Backdrop",
                "options": ["Textured Stone Panel", "Wood Slat Panel", "Fluted Panel + LED Strip", "Plain Paint"],
            },
        },
    },
    "Bathroom": {
        "icon": "🚿",
        "default_dims": {"length": 8.0, "width": 6.0, "height": 9.0},
        "fields": {
            "sanitaryware": {
                "label": "Sanitaryware Style",
                "options": ["Wall-hung", "Floor-mounted", "Premium Designer"],
            },
            "tiling": {
                "label": "Tiling",
                "options": ["Large Format Tiles", "Marble Look Tiles", "Mosaic Accent + Plain"],
            },
            "shower": {
                "label": "Shower Type",
                "options": ["Glass Enclosed Shower Cubicle", "Rain Shower (Open)", "Bathtub + Shower Combo"],
            },
        },
    },
}

DESIGN_STYLES = [
    "Modern Minimalist",
    "Contemporary",
    "Scandinavian",
    "Industrial",
    "Traditional Indian",
    "Mid-Century Modern",
    "Luxury Art Deco",
    "Japandi",
]

BUDGET_TIERS = ["Economy", "Standard", "Premium", "Luxury"]


# ============================================================
# AI SERVICE (provider abstraction + OpenAI implementation)
# ============================================================

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
    GPT Image 2 (current flagship image model, best photorealism and
    prompt adherence) for the preview render. Note: DALL-E 2/3 were
    removed from the OpenAI API in May 2026, so no fallback to those."""

    def __init__(self, api_key: Optional[str] = None,
                 text_model: str = "gpt-4o-mini",
                 image_model: str = "gpt-image-2",
                 image_quality: str = "high",
                 image_size: str = "1536x1024"):
        from openai import OpenAI  # imported lazily so app still loads without the package configured
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")
        self.client = OpenAI(api_key=self.api_key)
        self.text_model = text_model
        self.image_model = image_model
        self.image_quality = image_quality
        self.image_size = image_size

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
                size=self.image_size,
                quality=self.image_quality,
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


class HuggingFaceProvider(AIDesignProvider):
    """Uses Hugging Face Inference Providers: an open chat model for the
    design brief (OpenAI-compatible chat completions via HF's router) and
    FLUX.1-schnell (Black Forest Labs, Apache-2.0 — free for commercial
    use, fast) for the preview render. Needs only an HF_TOKEN, and HF's
    serverless free tier avoids the OpenAI billing/quota setup entirely."""

    def __init__(self, hf_token: Optional[str] = None,
                 text_model: str = "Qwen/Qwen2.5-7B-Instruct",
                 image_model: str = "black-forest-labs/FLUX.1-schnell"):
        from huggingface_hub import InferenceClient
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        if not self.hf_token:
            raise RuntimeError("HF_TOKEN is not set. Add it to your environment or .env file.")
        self.client = InferenceClient(api_key=self.hf_token)
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
            response = self.client.chat_completion(
                model=self.text_model,
                messages=[{"role": "user", "content": self._build_prompt(req)}],
                temperature=0.7,
                max_tokens=800,
            )
            raw_text = response.choices[0].message.content or ""
        except Exception as exc:
            logger.exception("Hugging Face text generation failed")
            return DesignResult(
                summary="", layout_plan="", materials=[], color_palette=[],
                estimated_cost_range="", raw_text="", error=str(exc),
            )

        data = _extract_json(raw_text)
        if data is None:
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
        result.__dict__["_image_prompt"] = data.get("image_prompt", "")
        return result

    def generate_preview_image(self, req: DesignRequest, recommendation: DesignResult) -> DesignResult:
        prompt = recommendation.__dict__.get("_image_prompt") or (
            f"Interior photo of a {req.style} {req.room_type}, {_area_sqft(req)} sq ft, "
            f"realistic architectural visualization, no text, no people"
        )
        try:
            image = self.client.text_to_image(prompt=prompt, model=self.image_model)
            import io as _io
            buf = _io.BytesIO()
            image.save(buf, format="PNG")
            recommendation.image_bytes = buf.getvalue()
        except Exception as exc:
            logger.exception("Hugging Face image generation failed")
            recommendation.error = (recommendation.error or "") + f" | Image generation failed: {exc}"
        return recommendation


class StubProvider(AIDesignProvider):
    """No-network fallback so the UI is fully explorable without an API key."""

    def generate_recommendation(self, req: DesignRequest) -> DesignResult:
        return DesignResult(
            summary=f"[Demo mode] A {req.style.lower()} {req.room_type.lower()} concept "
                     f"tailored to your {_area_sqft(req)} sq ft space.",
            layout_plan="Add HF_TOKEN (Hugging Face, free) or OPENAI_API_KEY to generate a real, dimension-aware layout plan.",
            materials=[v for v in req.selections.values()][:4],
            color_palette=["Warm White", "Charcoal Grey", "Brass Accents"],
            estimated_cost_range="₹1.5L - ₹3L (placeholder)",
            raw_text="",
        )

    def generate_preview_image(self, req: DesignRequest, recommendation: DesignResult) -> DesignResult:
        recommendation.error = "Demo mode: no image generated. Add HF_TOKEN (free) or OPENAI_API_KEY for AI renders."
        return recommendation


def _get_openai_key() -> Optional[str]:
    """Checks a plain environment variable first (local runs, .env),
    then Streamlit Cloud's secrets store, which is NOT the same as
    os.environ unless you've mirrored it there yourself."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except Exception:
        return None


def _get_hf_token() -> Optional[str]:
    """Checks a plain environment variable first, then Streamlit's secrets store."""
    token = os.environ.get("HF_TOKEN")
    if token:
        return token
    try:
        return st.secrets.get("HF_TOKEN")
    except Exception:
        return None


def get_provider() -> AIDesignProvider:
    """Factory: tries Hugging Face first (simplest setup, generous free
    tier), then OpenAI, then falls back to the stub so the app never
    hard-crashes without any key configured."""
    hf_token = _get_hf_token()
    if hf_token:
        try:
            return HuggingFaceProvider(hf_token=hf_token)
        except Exception as exc:
            logger.exception("Hugging Face provider init failed, trying OpenAI")
            st.session_state["_provider_init_error"] = f"Hugging Face: {exc}"

    api_key = _get_openai_key()
    if api_key:
        try:
            return OpenAIProvider(api_key=api_key)
        except Exception as exc:
            logger.exception("Falling back to StubProvider")
            st.session_state["_provider_init_error"] = str(exc)
            return StubProvider()

    if not hf_token and "OPENAI_API_KEY" not in os.environ:
        st.session_state["_provider_init_error"] = (
            "No HF_TOKEN or OPENAI_API_KEY found in environment variables or st.secrets."
        )
    return StubProvider()


# ============================================================
# UTILS (session state + export)
# ============================================================

def init_session_state():
    if "apartment" not in st.session_state:
        st.session_state.apartment = {
            "name": "My New Apartment",
            "total_area_sqft": 1200,
            "num_bedrooms": 2,
        }
    if "room_designs" not in st.session_state:
        # room_name -> {"request": DesignRequest-as-dict, "result": DesignResult-as-dict}
        st.session_state.room_designs = {}
    if "room_dims" not in st.session_state:
        st.session_state.room_dims = {}


def save_room_design(room_name: str, request_dict: dict, result_dict: dict):
    st.session_state.room_designs[room_name] = {
        "request": request_dict,
        "result": result_dict,
    }


def get_room_design(room_name: str):
    return st.session_state.room_designs.get(room_name)


def export_summary_json() -> bytes:
    payload = {
        "apartment": st.session_state.apartment,
        "rooms": st.session_state.room_designs,
    }
    return json.dumps(payload, indent=2, default=str).encode("utf-8")


def export_summary_markdown() -> bytes:
    lines = [f"# Design Summary — {st.session_state.apartment.get('name', 'Apartment')}\n"]
    lines.append(f"Total area: {st.session_state.apartment.get('total_area_sqft')} sq ft\n")
    for room, data in st.session_state.room_designs.items():
        req = data["request"]
        res = data["result"]
        lines.append(f"\n## {room}")
        lines.append(f"- Dimensions: {req.get('length_ft')} ft x {req.get('width_ft')} ft "
                      f"(height {req.get('height_ft')} ft)")
        lines.append(f"- Style: {req.get('style')} | Budget: {req.get('budget_tier')}")
        if req.get("selections"):
            lines.append("- Selections:")
            for k, v in req["selections"].items():
                lines.append(f"  - {k}: {v}")
        if res.get("summary"):
            lines.append(f"\n**Summary:** {res['summary']}")
        if res.get("layout_plan"):
            lines.append(f"\n**Layout Plan:** {res['layout_plan']}")
        if res.get("materials"):
            lines.append(f"\n**Materials:** {', '.join(res['materials'])}")
        if res.get("color_palette"):
            lines.append(f"\n**Color Palette:** {', '.join(res['color_palette'])}")
        if res.get("estimated_cost_range"):
            lines.append(f"\n**Estimated Cost:** {res['estimated_cost_range']}")
    return "\n".join(lines).encode("utf-8")


# ============================================================
# STREAMLIT APP
# ============================================================

init_session_state()
provider = get_provider()
USING_STUB = provider.__class__.__name__ == "StubProvider"


# ---------------------------------------------------------------- Sidebar
st.sidebar.title("🏢 Apartment Designer")
if USING_STUB:
    reason = st.session_state.get("_provider_init_error", "No OPENAI_API_KEY detected.")
    st.sidebar.warning(f"Demo mode — {reason}", icon="⚠️")

nav_options = ["🏠 Apartment Setup"] + [
    f"{cfg['icon']} {room}" for room, cfg in ROOM_CONFIG.items()
] + ["📋 Summary & Export"]

page = st.sidebar.radio("Go to", nav_options, label_visibility="collapsed")

st.sidebar.divider()
completed = len(st.session_state.room_designs)
st.sidebar.caption(f"Rooms designed: {completed} / {len(ROOM_CONFIG)}")
st.sidebar.progress(completed / len(ROOM_CONFIG) if ROOM_CONFIG else 0)


# ---------------------------------------------------------------- Apartment Setup page
def render_setup_page():
    st.title("🏠 Apartment Setup")
    st.caption("Start here — set your apartment basics, then customize each room using its exact dimensions.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.apartment["name"] = st.text_input(
            "Apartment / Project name", value=st.session_state.apartment["name"]
        )
    with col2:
        st.session_state.apartment["total_area_sqft"] = st.number_input(
            "Total carpet area (sq ft)", min_value=200, max_value=10000,
            value=st.session_state.apartment["total_area_sqft"], step=50,
        )
    with col3:
        st.session_state.apartment["num_bedrooms"] = st.number_input(
            "Number of bedrooms", min_value=1, max_value=6,
            value=st.session_state.apartment["num_bedrooms"], step=1,
        )

    st.divider()
    st.subheader("Overall design preference (used as default for every room)")
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.session_state.setdefault("default_style", DESIGN_STYLES[0])
        st.session_state.default_style = st.selectbox("Preferred design style", DESIGN_STYLES,
                                                        index=DESIGN_STYLES.index(st.session_state.default_style))
    with dcol2:
        st.session_state.setdefault("default_budget", BUDGET_TIERS[1])
        st.session_state.default_budget = st.selectbox("Budget tier", BUDGET_TIERS,
                                                         index=BUDGET_TIERS.index(st.session_state.default_budget))

    st.info("Use the sidebar to open each room (Bedroom, Hall, Kitchen, Doors, Windows, TV Unit, Bathroom) "
            "and customize it based on its real dimensions.")


# ---------------------------------------------------------------- Generic room page
def render_room_page(room_name: str):
    cfg = ROOM_CONFIG[room_name]
    st.title(f"{cfg['icon']} {room_name}")

    dims_key = room_name
    saved_dims = st.session_state.room_dims.get(dims_key, cfg["default_dims"])

    st.subheader("1. Room Dimensions")
    d1, d2, d3 = st.columns(3)
    with d1:
        length = st.number_input("Length (ft)", min_value=1.0, max_value=60.0,
                                  value=float(saved_dims["length"]), step=0.5, key=f"{room_name}_len")
    with d2:
        width = st.number_input("Width (ft)", min_value=0.2, max_value=60.0,
                                 value=float(saved_dims["width"]), step=0.5, key=f"{room_name}_wid")
    with d3:
        height = st.number_input("Height (ft)", min_value=6.0, max_value=20.0,
                                  value=float(saved_dims["height"]), step=0.5, key=f"{room_name}_hgt")
    st.session_state.room_dims[dims_key] = {"length": length, "width": width, "height": height}
    if width > 0.9:  # skip trivial area display for doors/windows which use width as thickness
        st.caption(f"Approx. area: **{round(length * width, 1)} sq ft**")

    st.subheader("2. Style & Budget")
    s1, s2 = st.columns(2)
    with s1:
        style = st.selectbox("Design style", DESIGN_STYLES,
                              index=DESIGN_STYLES.index(st.session_state.get("default_style", DESIGN_STYLES[0])),
                              key=f"{room_name}_style")
    with s2:
        budget = st.selectbox("Budget tier", BUDGET_TIERS,
                               index=BUDGET_TIERS.index(st.session_state.get("default_budget", BUDGET_TIERS[1])),
                               key=f"{room_name}_budget")

    st.subheader("3. Customize")
    selections = {}
    field_items = list(cfg["fields"].items())
    cols = st.columns(2)
    for i, (field_key, field_def) in enumerate(field_items):
        with cols[i % 2]:
            selections[field_key] = st.selectbox(
                field_def["label"], field_def["options"], key=f"{room_name}_{field_key}"
            )

    notes = st.text_area("Anything specific to mention? (optional)",
                          placeholder="e.g. 'need extra storage', 'north-facing wall', 'kids allergic to strong paint smell'",
                          key=f"{room_name}_notes")

    st.divider()
    qcol1, qcol2 = st.columns([1, 2])
    with qcol1:
        render_quality = st.radio(
            "Preview quality",
            ["Draft (fast, cheaper)", "Final (high quality)"],
            key=f"{room_name}_quality",
            horizontal=False,
        )
    with qcol2:
        st.caption("Use Draft while you're still tweaking materials and layout, "
                    "then switch to Final for the polished render.")
    generate = st.button(f"✨ Generate AI Design for {room_name}", type="primary", key=f"{room_name}_generate")

    existing = get_room_design(room_name)

    if generate:
        req = DesignRequest(
            room_type=room_name, length_ft=length, width_ft=width, height_ft=height,
            style=style, budget_tier=budget, selections=selections, notes=notes,
        )
        is_final = render_quality.startswith("Final")
        if isinstance(provider, OpenAIProvider):
            provider.image_quality = "high" if is_final else "medium"
        with st.spinner("Designing your space..."):
            result = provider.generate_recommendation(req)
            if not result.error or "Could not fully parse" in (result.error or ""):
                result = provider.generate_preview_image(req, result)

        save_room_design(room_name, req.__dict__, result.__dict__)
        existing = get_room_design(room_name)

    if existing:
        result = existing["result"]
        st.subheader("AI Design Recommendation")

        if result.get("error") and not result.get("summary"):
            st.error(result["error"])
        else:
            if result.get("error"):
                st.caption(f"⚠️ {result['error']}")

            rc1, rc2 = st.columns([1, 1])
            with rc1:
                if result.get("summary"):
                    st.markdown(f"**Concept:** {result['summary']}")
                if result.get("layout_plan"):
                    st.markdown(f"**Layout Plan:** {result['layout_plan']}")
                if result.get("materials"):
                    st.markdown("**Materials:**")
                    for m in result["materials"]:
                        st.markdown(f"- {m}")
                if result.get("color_palette"):
                    st.markdown("**Color Palette:** " + ", ".join(result["color_palette"]))
                if result.get("estimated_cost_range"):
                    st.metric("Estimated cost for this room", result["estimated_cost_range"])
            with rc2:
                if result.get("image_bytes"):
                    st.image(result["image_bytes"], caption=f"AI preview — {room_name}", use_container_width=True)
                elif result.get("image_url"):
                    st.image(result["image_url"], caption=f"AI preview — {room_name}", use_container_width=True)
                else:
                    st.caption("No preview image available for this design.")


# ---------------------------------------------------------------- Summary page
def render_summary_page():
    st.title("📋 Summary & Export")
    if not st.session_state.room_designs:
        st.info("You haven't generated any room designs yet. Pick a room from the sidebar to get started.")
        return

    st.write(f"**{st.session_state.apartment['name']}** — "
             f"{st.session_state.apartment['total_area_sqft']} sq ft, "
             f"{st.session_state.apartment['num_bedrooms']} bedrooms")

    for room, data in st.session_state.room_designs.items():
        req, res = data["request"], data["result"]
        with st.expander(f"{room} — {req.get('style', '')}", expanded=False):
            c1, c2 = st.columns([1, 1])
            with c1:
                st.write(f"Dimensions: {req.get('length_ft')} ft x {req.get('width_ft')} ft "
                         f"(height {req.get('height_ft')} ft)")
                if res.get("summary"):
                    st.write(res["summary"])
                if res.get("estimated_cost_range"):
                    st.write(f"**Estimated cost:** {res['estimated_cost_range']}")
            with c2:
                if res.get("image_bytes"):
                    st.image(res["image_bytes"], use_container_width=True)
                elif res.get("image_url"):
                    st.image(res["image_url"], use_container_width=True)

    st.divider()
    st.subheader("Export")
    ecol1, ecol2 = st.columns(2)
    with ecol1:
        st.download_button("⬇️ Download JSON", data=export_summary_json(),
                            file_name="apartment_design_summary.json", mime="application/json")
    with ecol2:
        st.download_button("⬇️ Download Markdown Report", data=export_summary_markdown(),
                            file_name="apartment_design_summary.md", mime="text/markdown")


# ---------------------------------------------------------------- Router
if page == "🏠 Apartment Setup":
    render_setup_page()
elif page == "📋 Summary & Export":
    render_summary_page()
else:
    room_name = page.split(" ", 1)[1]
    render_room_page(room_name)
