# Handover — Nimmy_McNimFace

Lean by design: only the ephemeral delta not already in [onboarding.md](../../onboarding.md),
[README.md](../../README.md), or [DEVLOG.md](DEVLOG.md). Read those first.

## State as of 2026-06-30

Just **graduated from The_Lab to its own public repo** (github.com/berad217/Nimmy_McNimFace)
and added an MIT LICENSE. The kit is complete and working; this is maintenance phase.

## In flight / unresolved (the stuff not captured elsewhere)

- **The rich arrow-key UI of `menu.py` and `chat.py` has never been run interactively.** It
  was only ever exercised via the numbered/piped fallback (which is fully tested). `questionary`
  needs a real Windows console (PowerShell / cmd / Windows Terminal); it falls back gracefully
  elsewhere. If verifying: `python menu.py` in a real console and confirm arrow keys + type-to-
  filter render. This is the one untested surface.
- **`05_speech.py` (Parakeet) is the only demo not green** — it needs the model's gRPC
  `function-id` (a UUID on the JS-rendered build.nvidia.com model page) pasted into `nim.py`'s
  `PARAKEET_FUNCTION_ID`, plus `pip install nvidia-riva-client`.
- **`_CHAT_YEAR` in `menu.py` is hand-tuned and approximate** — years for post-training-cutoff
  models default to the newest bucket. If a model lands in the wrong era, it's a one-line edit.

## Intended next move

Wire this into **caption_lab** (Brad's other project, which already has a few VLM solutions —
this becomes another). Recipe is in [docs/multimodal.md](multimodal.md): import `nim.py`, pick
a fast model from `VISION_CAPABLE` (default `google/gemma-4-31b-it`), batch via fresh calls.

## Note

A stale duplicate may still exist at `P:\software_projects\The_Lab\nvidia_demos\` (was locked
by an open VS Code editor at graduation). It's safe to delete; this repo is the canonical copy.
