"""Interactive terminal model picker for the NVIDIA NIM demos.

Arrow-key menu: pick a modality, then a model. Chat is huge (~105), so it gets an
extra "era" step first -- 2026+ / 2025 / pre-2025 / specialty -- to keep the default
list short; see _CHAT_YEAR / _CHAT_SPECIALTY for the (tunable) year assignments.
The Shape-1 lists (chat / vision / embedding) are pulled LIVE from the API via
nim.list_models(), so they always reflect the current offerings. The non-discoverable
Shape-2/3 models (rerank / image / speech) come from nim.CURATED_MODELS.

On selection it prints the slug plus a ready-to-paste call into the matching nim.py
helper. Run it:  python menu.py

Arrow-key picking needs a real Windows console (PowerShell / cmd / Windows Terminal).
In Git Bash, a piped stdin, or anywhere prompt_toolkit can't grab a console, it falls
back automatically to a numbered list (with a substring filter for long lists).

From the model menu, the first entry ("<- back to modalities") returns to stage 1.
Quit any prompt with Ctrl-C (or 'q' / blank at the numbered fallback).
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict

import questionary

import nim

# Flips to True the first time questionary can't grab a console, so we don't keep
# retrying the rich picker prompt-by-prompt -- one failure, numbered list thereafter.
_USE_NUMBERED = False

# Sentinel returned by the model menu's "back" entry -> bounce up to the modality menu.
_BACK = object()

# One snippet template per modality -> the nim.py helper that drives that shape.
# {slug} is filled with the chosen model id.
_SNIPPETS = {
    "chat":      'nim.chat("Hello!", model="{slug}")',
    "vision":    'nim.describe_image("doc_sample.png", "What is this?", model="{slug}")',
    "embedding": 'nim.embed(["some text"], model="{slug}")',
    "rerank":    'nim.rerank("query", ["passage a", "passage b"], model="{slug}")',
    "image":     'nim.generate_image("a red bicycle", model_path="{slug}")',
    "speech":    'nim.transcribe("audio.wav")  # also paste the model\'s function-id',
}

# Display order for the modality menu (and the curated tail).
_MODALITY_ORDER = ["chat", "vision", "embedding", "rerank", "image", "speech"]

# --- Chat bucketing -------------------------------------------------------------
# Chat is the only oversized bucket (~105 models). We split it by release era so the
# newest generation shows first. There's NO date in the API (the `created` field is a
# frozen constant), so the year is assigned by hand below -- but only for models old
# enough to be datable. Anything unknown defaults to the NEWEST bucket: a model not in
# the map is assumed brand-new (post-training-cutoff), so new offerings auto-surface and
# we never fabricate a year for a model we can't actually place.
#
# Two knobs: _CHAT_SPECIALTY (pulled out regardless of year) and _CHAT_YEAR (per-model
# year overrides, regex -> year). Slugs carrying a Mistral-style YYMM stamp (e.g.
# '...-2512') are dated straight from the stamp -- a real signal, not a guess.
_CHAT_BUCKETS = ["2026+", "2025", "pre-2025", "specialty"]  # display order, newest first

# Special-purpose models that aren't general chat (safety / guard / reward / translate / parse).
_CHAT_SPECIALTY = [
    r"guard", r"safety", r"-pii", r"gliner", r"reward", r"synthetic-video",
    r"topic-control", r"calibration", r"riva-translate", r"chatqa",
    r"nemotron-parse", r"nemoretriever-parse",
]

# Release year per model, for those datable from training or a slug stamp. Regex keys are
# anchored where a family spans eras -- e.g. 'mistral-nemo-' must not catch the newer
# 'mistral-nemotron'. Not listed (and no YYMM stamp) => newest bucket.
_CHAT_YEAR = {
    # --- pre-2025 (2024 and older) ---
    r"meta/llama2": 2023, r"meta/codellama": 2023, r"deepseek-coder": 2023,
    r"kosmos": 2023, r"mixtral": 2023, r"fuyu": 2023, r"deplot": 2023,
    r"yi-large": 2024, r"dracarys": 2024, r"jamba": 2024, r"sea-lion": 2024,
    r"starcoder": 2024, r"dbrx": 2024, r"codegemma": 2024, r"gemma-2": 2024,
    r"recurrentgemma": 2024, r"granite-3\.0": 2024, r"granite-.*-code": 2024,
    r"meta/llama-3": 2024, r"phi-3": 2024, r"codestral": 2024, r"mistral-7b": 2024,
    r"mistralai/mistral-large(-2)?(-instruct)?$": 2024, r"mistral-nemo-": 2024,
    r"minitron": 2024, r"llama-3\.1-nemotron": 2024, r"nemotron-4-340b": 2024,
    r"nemotron-mini": 2024, r"/neva": 2024, r"/vila": 2024, r"nvclip": 2024,
    r"solar-": 2024, r"palmyra-med-70b": 2024, r"palmyra-fin": 2024, r"zamba": 2024,
    # --- 2025 ---
    r"llama-4": 2025, r"gemma-3": 2025, r"phi-4": 2025, r"qwen3-next": 2025,
    r"gpt-oss": 2025, r"mistral-medium-3\.5": 2025, r"mistral-nemotron": 2025,
    r"llama-3\.3-nemotron": 2025, r"nemotron-nano-9b-v2": 2025, r"nemotron-nano-12b": 2025,
    r"cosmos-reason": 2025, r"palmyra-creative": 2025, r"sarvam-m": 2025,
    r"seed-oss": 2025, r"stockmark-2": 2025,
}


def _stamp_year(slug: str) -> int | None:
    """Pull a year from a Mistral-style YYMM date stamp in the slug (e.g. -2512 -> 2025)."""
    m = re.search(r"-(\d{2})(\d{2})\b", slug)
    if m and 1 <= int(m.group(2)) <= 12:
        return 2000 + int(m.group(1))
    return None


def _chat_bucket(slug: str) -> str:
    """Classify a chat slug into a release-era bucket ('2026+', '2025', 'pre-2025') or 'specialty'."""
    s = slug.lower()
    if any(re.search(p, s) for p in _CHAT_SPECIALTY):
        return "specialty"
    year = next((y for p, y in _CHAT_YEAR.items() if re.search(p, s)), None)
    year = year or _stamp_year(s) or 2026  # unknown -> newest
    return "2026+" if year >= 2026 else ("2025" if year == 2025 else "pre-2025")


def _numbered_pick(message: str, choices: list[questionary.Choice]):
    """Plain-stdin fallback picker. Returns the chosen .value, or None to quit.

    For long lists (>20) it first asks for a case-insensitive substring filter so you
    don't scroll past 100 chat models. Blank / 'q' / EOF at the number prompt quits.
    """
    print(f"\n{message}")
    items = choices
    try:
        if len(items) > 20:
            flt = input("  filter (substring, Enter for all): ").strip().lower()
            if flt:
                matches = [c for c in choices if flt in c.title.lower()]
                if matches:
                    items = matches
                else:
                    print("  no matches; showing all")
        for i, c in enumerate(items, 1):
            print(f"  {i:>3}. {c.title}")
        while True:
            raw = input("  number (q to quit): ").strip()
            if raw.lower() in ("q", ""):
                return None
            if raw.isdigit() and 1 <= int(raw) <= len(items):
                return items[int(raw) - 1].value
            print("  invalid choice")
    except EOFError:  # piped/redirected stdin with nothing to read
        return None


def _pick(message: str, choices: list[questionary.Choice], searchable: bool = False):
    """Arrow-key picker via questionary; auto-fall-back to numbered list with no console."""
    global _USE_NUMBERED
    if not _USE_NUMBERED:
        try:
            kwargs = {"use_search_filter": True, "use_jk_keys": False} if searchable else {}
            return questionary.select(message, choices=choices, **kwargs).ask()
        except Exception:  # noqa: BLE001 -- no usable console; degrade, don't crash
            _USE_NUMBERED = True
            print("(no interactive console -- falling back to a numbered list)")
    return _numbered_pick(message, choices)


def _pick_chat(bucket: list[dict]):
    """Two-step chat picker: release era (2026+ / 2025 / pre-2025 / specialty) -> model.

    Returns a model dict, _BACK (caller should go up to the modality menu), or
    None (quit). 'back' inside the model list returns to the era menu.
    """
    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for m in bucket:
        by_bucket[_chat_bucket(m["id"])].append(m)

    while True:  # era level
        era_choices = [questionary.Choice("<- back to modalities", value=_BACK)] + [
            questionary.Choice(f"{b:<9} ({len(by_bucket[b])})", value=b)
            for b in _CHAT_BUCKETS if by_bucket[b]
        ]
        era = _pick("Pick a chat era (newest first):", era_choices)
        if era is None:      # quit
            return None
        if era is _BACK:     # up to modality menu
            return _BACK

        model = _pick(
            f"Pick a {era} chat model (type to filter):",
            [questionary.Choice("<- back to eras", value=_BACK)]
            + [questionary.Choice(m["id"], value=m) for m in by_bucket[era]],
            searchable=True,
        )
        if model is None:     # quit
            return None
        if model is _BACK:    # back to era menu
            continue
        return model


def _all_models() -> list[dict]:
    """Live Shape-1 catalog + curated Shape-2/3, unified to {id, modality, shape}."""
    live = [
        {"id": m["id"], "modality": m["modality"], "shape": "openai"}
        for m in nim.list_models()
    ]
    return live + nim.CURATED_MODELS


def main() -> int:
    try:
        print("Fetching live model catalog from NVIDIA ...")
        models = _all_models()
    except Exception as exc:  # noqa: BLE001 -- surface any fetch/auth failure plainly
        print(f"Could not load models: {exc}", file=sys.stderr)
        return 1

    by_modality: dict[str, list[dict]] = {}
    for m in models:
        by_modality.setdefault(m["modality"], []).append(m)

    # "vision" is a cross-cutting *capability* view, not an exclusive bucket. The slug
    # heuristic only catches dedicated VLMs (vision/vlm/...); nim.VISION_CAPABLE adds the
    # modern multimodal chat models (gemma-4, qwen3.5, ...) that read images but are
    # primarily 'chat'. They stay in chat too -- here we just also list them under vision.
    by_id = {m["id"]: m for m in models}
    vision_ids = {m["id"] for m in by_modality.get("vision", [])}
    for vid in nim.VISION_CAPABLE:
        if vid in by_id and vid not in vision_ids:
            by_modality.setdefault("vision", []).append(by_id[vid])
            vision_ids.add(vid)

    # Stage 1: pick a modality (show counts so the size of each bucket is obvious).
    modality_choices = [
        questionary.Choice(f"{mod:<10} ({len(by_modality[mod])})", value=mod)
        for mod in _MODALITY_ORDER
        if mod in by_modality
    ]
    while True:
        # Stage 1: pick a modality.
        modality = _pick("Pick a modality:", modality_choices)
        if modality is None:  # Ctrl-C / quit
            return 130

        # Stage 2: pick a model. A "back" entry returns the _BACK sentinel (not quit)
        # so we re-loop to stage 1. Chat is huge, so it gets a tier sub-level first;
        # every other modality is small enough to pick directly.
        bucket = sorted(by_modality[modality], key=lambda m: m["id"])
        if modality == "chat":
            model = _pick_chat(bucket)
        else:
            model = _pick(
                f"Pick a {modality} model (type to filter):",
                [questionary.Choice("<- back to modalities", value=_BACK)]
                + [questionary.Choice(m["id"], value=m) for m in bucket],
                searchable=True,
            )
        if model is None:  # Ctrl-C / quit at the model menu
            return 130
        if model is _BACK:
            continue
        break

    snippet = _SNIPPETS[modality].format(slug=model["id"])
    print("\n" + "-" * 60)
    print(f"  model    : {model['id']}")
    print(f"  modality : {modality}   (call shape: {model['shape']})")
    print(f"  use it   : {snippet}")
    print("-" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
