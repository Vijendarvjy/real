# AI Apartment Interior Designer

A Streamlit app for selecting and customizing interior designs — bedrooms,
hall/living room, kitchen, doors, windows, TV unit, bathroom — based on
actual room dimensions, with AI-generated recommendations and preview
render images (OpenAI GPT + gpt-image-1 / DALL-E).

## Setup

```bash
cd apartment_designer
pip install -r requirements.txt
```

Set your OpenAI API key (the app runs in demo mode without it — full UI,
placeholder recommendations, no real images):

```bash
export OPENAI_API_KEY="sk-..."          # macOS/Linux
setx OPENAI_API_KEY "sk-..."            # Windows (new terminal after)
```

Or create a `.env` file in this folder:
```
OPENAI_API_KEY=sk-...
```
and load it before running (add `from dotenv import load_dotenv; load_dotenv()`
to the top of `app.py` if you prefer `.env` over environment variables).

## Run

```bash
streamlit run app.py
```

## How it works

1. **Apartment Setup** — set project name, total area, bedroom count, and a
   default style/budget used to pre-fill every room.
2. **Per-room pages** (sidebar) — each room (Master Bedroom, Kids Bedroom,
   Living/Hall, Kitchen, Doors, Windows, TV/Media Unit, Bathroom) has:
   - Editable length/width/height inputs (defaults provided, area auto-calculated)
   - Style + budget tier selectors
   - Room-specific customization fields (materials, layouts, finishes —
     defined in `config.py`, easy to extend)
   - An "Generate AI Design" button that calls OpenAI to produce a JSON
     design brief (concept, layout plan, materials, color palette, cost
     estimate) and then generates a preview image from that brief
3. **Summary & Export** — see every designed room in one place and download
   a JSON or Markdown report of the whole apartment.

## Architecture notes

- `config.py` — all room types, dimensions, and customization options live
  here. Add a new room or field by editing this dict; no UI code changes needed.
- `ai_service.py` — the AI vendor is abstracted behind `AIDesignProvider`
  (`generate_recommendation`, `generate_preview_image`). `OpenAIProvider`
  implements it today; swap in Azure OpenAI, Stability, or any other vendor
  by writing a new class with the same interface and updating `get_provider()`.
  A `StubProvider` fallback means the app never hard-crashes without a key.
- JSON parsing from the LLM response walks brace-depth to find the first
  valid JSON object (models sometimes wrap responses in prose/markdown),
  with a regex fallback if parsing still fails.
- `utils.py` — Streamlit session-state helpers and export (JSON/Markdown).

## Extending

- **More rooms**: add an entry to `ROOM_CONFIG` in `config.py`.
- **Different AI vendor**: implement `AIDesignProvider` in `ai_service.py`
  and swap it in `get_provider()`.
- **Cost estimation**: currently the LLM estimates a cost range in its
  response; swap in a real pricing table keyed by material/area if you want
  deterministic quotes instead.
- **Persistence**: session state resets on browser refresh. Wire `utils.py`
  to a database (e.g. your existing PostgreSQL setup) to persist a client's
  selections across sessions.
