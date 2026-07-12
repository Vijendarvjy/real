"""
AI Apartment Interior Designer
A Streamlit app for selecting and customizing interior designs (bedrooms,
hall, kitchen, doors, windows, TV unit, bathroom) based on actual room
dimensions, with AI-generated recommendations and preview renders.
"""

import streamlit as st

from config import ROOM_CONFIG, DESIGN_STYLES, BUDGET_TIERS
from ai_service import get_provider, DesignRequest
from utils import init_session_state, save_room_design, get_room_design, export_summary_json, export_summary_markdown

st.set_page_config(
    page_title="AI Apartment Designer",
    page_icon="🏢",
    layout="wide",
)

init_session_state()
provider = get_provider()
USING_STUB = provider.__class__.__name__ == "StubProvider"


# ---------------------------------------------------------------- Sidebar
st.sidebar.title("🏢 Apartment Designer")
if USING_STUB:
    st.sidebar.warning("Demo mode — set OPENAI_API_KEY to enable real AI "
                        "recommendations and image renders.", icon="⚠️")

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
    generate = st.button(f"✨ Generate AI Design for {room_name}", type="primary", key=f"{room_name}_generate")

    existing = get_room_design(room_name)

    if generate:
        req = DesignRequest(
            room_type=room_name, length_ft=length, width_ft=width, height_ft=height,
            style=style, budget_tier=budget, selections=selections, notes=notes,
        )
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
