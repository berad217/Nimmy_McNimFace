# Tasks — Nimmy_McNimFace

## Active

- [ ] Wire NIM captioning into **caption_lab** (import `nim.py`; see [docs/multimodal.md](docs/multimodal.md)).
- [ ] Verify the interactive `menu.py` / `chat.py` UI in a real Windows console (only the numbered fallback has been tested).
- [ ] Finish `05_speech.py`: paste Parakeet's gRPC `function-id` into `nim.py`, `pip install nvidia-riva-client`.

## Someday

- [ ] New demos from the catalog: BioNeMo (protein/molecule), Canary (multilingual ASR), TTS (Magpie/FastPitch), Nemotron VL/OCR.
- [ ] Tune `_CHAT_YEAR` era assignments as the catalog shifts (only matters if a model shows up in the wrong era bucket).

## Done

- [x] 2026-06-30 — Graduated from The_Lab to its own public GitHub repo + MIT license.
- [x] 2026-06-30 — Model menu (`menu.py`) with chat "era" buckets + numbered fallback.
- [x] 2026-06-30 — Multi-turn chat / captioning (`ChatSession`, `chat.py`, `VISION_CAPABLE`, docs/multimodal.md).
- [x] 2026-06-23 — Initial 6-demo kit, one key / three call shapes.
