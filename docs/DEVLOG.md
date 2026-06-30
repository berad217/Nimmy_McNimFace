# DEVLOG — Nimmy_McNimFace

Newest first. One entry per meaningful session: what was built and *why*.

## 2026-06-30 — Graduated out of The_Lab; menu + multimodal toolkit

Spiked originally in `The_Lab/nvidia_demos/`; grew real structure, so it graduated to its
own repo (`berad217/Nimmy_McNimFace`, public).

Built this session, on top of the existing 6 demos:
- **`nim.list_models()`** — live `GET /v1/models` catalog, modality-tagged. Discovered the
  API's `created` field is a frozen constant (no real dates) and that `/v1/models` is **Shape 1
  only** (rerank/image/speech aren't listed anywhere → `CURATED_MODELS`).
- **`menu.py`** — interactive picker. Chat (~105 models) was an unusable wall, so it gets an
  **"era" sub-menu** (2026+ / 2025 / pre-2025 / specialty). No dates in the API, so years are
  hand-assigned in `_CHAT_YEAR` with a Mistral-style `YYMM`-stamp parser; unknown → newest
  bucket (new models auto-surface). Numbered fallback for no-console shells; back-navigation.
- **`nim.ChatSession` + `chat.py`** — multi-turn chat with image attach (ollama-style REPL).
  Fixed a latent streaming bug (NIM sends a final chunk with empty `choices`; `chunk.choices[0]`
  was crashing — guarded in both `chat()` and `ChatSession`).
- **`nim.VISION_CAPABLE` + `docs/multimodal.md`** — the API exposes no capability metadata, so
  image-accepting models are a curated list. Doc is the wiring guide for downstream projects
  (caption_lab will consume this). `menu.py`'s vision tab is now a cross-cutting capability view
  driven by that list.

Measured gotcha worth keeping: model latency varies wildly (mistral-small-4 ~1.7s vs
qwen3.5-122b ~94s for one caption — the latter is a reasoning model). Pick fast models for batch.

## 2026-06-23 — Initial demo kit (in The_Lab)

Six minimal demos, one per modality, all sharing `nim.py` (the three-call-shape wrapper).
01–04 and 06 tested live; 05 (Parakeet speech) needs a gRPC `function-id` pasted in. First
run surfaced one EOL slug (an embedder retired 2026-05-18) — confirmed the "slug as named
constant, fix in one line" approach.
