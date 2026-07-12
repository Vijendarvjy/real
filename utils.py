"""Session-state helpers and export utilities."""

import json
import io
import streamlit as st


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
