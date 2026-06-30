# 🟩 Nimmy_McNimFace

**One free API key. 120+ AI models. Chat, vision, image-gen, speech, embeddings, reranking, doc-parsing — all of it.**

Nimmy is a small, honest toolbox for NVIDIA's [build.nvidia.com](https://build.nvidia.com)
catalog (a.k.a. "NIM"). One `nvapi-` key unlocks **the whole zoo**: 100+ chat LLMs, a pile
of vision models, FLUX for images, Parakeet for speech, embedders, rerankers, the works.
**40 requests/min, no token cap, no credit card.** It is the most generous free deal going
for *breadth* of models — you trade a little raw speed for it (Groq/Cerebras are faster, on
far fewer models).

The catch isn't the code. The catch is **getting the key** (see the obstacle course below).
Once you have it, everything here is ~15 lines per call.

> Built as a reference kit so my other projects — and the agents working on them — can wire
> NIM in without rediscovering every gotcha. If you found this on the internet: hi, it works,
> the docs are real, help yourself.

---

## 🗝️ Getting an NVIDIA key: the obstacle course

Yes. There **is** a key at the end of this. It's free, it's real, and it starts with
`nvapi-`. NVIDIA just makes you earn it. Here's the course — treat the clicks as
*landmarks*, because NVIDIA rearranges this furniture roughly once a quarter.

1. **Go to [build.nvidia.com](https://build.nvidia.com).** Not NGC, not the Developer
   Program portal, not the Enterprise thing. *This* site. (They have nine doors; this is
   the one that gives out free keys.)
2. **Make an account / log in.** A personal email works — you do **not** need a corporate
   one, whatever the form implies. Verify the email when it lands.
3. **Suffer the profile form.** Name, country, and a "company/organization" it won't let
   you skip. Type `Individual` or `Personal` and move on; nobody checks.
4. **Pick any model** from the catalog (e.g. *Llama 3.3 70B*). You land on its page with a
   chat box and, off to the side, a **code panel**.
5. **Click "Get API Key"** (sometimes "Build with this NIM" → "Get API Key"). A key starting
   `nvapi-` appears.
6. **COPY IT NOW.** It is shown **once**. Close the dialog without copying and you start over
   with a fresh one. Don't be a hero.

**Gotchas that waste an afternoon:**

- **`nvapi-` is the one you want.** NGC has an older "API key" concept that looks similar and
  is *not* the same thing. If your key doesn't start `nvapi-`, you grabbed the wrong artifact.
- **One key, the whole catalog.** You do **not** generate a key per model. The key you minted
  on the Llama page also talks to FLUX, Parakeet, and everything else.
- **Free credits, not unlimited.** The free tier is a generous bucket of requests, not a
  bottomless one. Plenty for tinkering; don't point a batch job at it and walk away.

Then:

    cp .env.example .env     # paste the key here

```
NVIDIA_API_KEY=nvapi-...
```

That's the last hard part. Everything below is easy.

---

## 🚀 Quickstart

    pip install -r requirements.txt
    cp .env.example .env        # paste your nvapi- key (see obstacle course above)
    python 01_chat.py           # prove the key works
    python menu.py              # browse the live model catalog, get a paste-ready call
    python chat.py photo.png    # multi-turn chat / image captioning REPL (ollama-style)

---

## 🧩 The one thing to understand: one key, three call shapes

The single key authenticates everything, but the *code shape* differs by modality. This is
the whole mental model:

| Shape | Transport | Used by | Endpoint |
|---|---|---|---|
| **1. OpenAI-compatible** | `openai` SDK | chat, vision, embeddings, doc-parse | `integrate.api.nvidia.com/v1` |
| **2. Plain REST** | `requests` | reranking, image generation | `ai.api.nvidia.com/v1/...` |
| **3. gRPC (Riva)** | `nvidia-riva-client` | speech / ASR | `grpc.nvcf.nvidia.com:443` |

[`nim.py`](nim.py) wraps all three so each demo file stays tiny.

## 🎬 The demos (one per modality)

| File | Modality | Default model (swap freely) | Shape | Good for | Status |
|---|---|---|---|---|---|
| [`01_chat.py`](01_chat.py) | LLM text | llama-3.3-70b | 1 | chatbots, generation, Q&A | ✅ tested |
| [`02_vision.py`](02_vision.py) | Vision-language | llama-3.2-11b-vision | 1 | image Q&A, captioning | ✅ tested |
| [`03_rag.py`](03_rag.py) | Embed + rerank | llama-nemotron-embed/-rerank | 1+2 | RAG, semantic search | ✅ tested |
| [`04_image.py`](04_image.py) | Text-to-image | FLUX.1-dev | 2 | art, sprites, mockups | ✅ tested |
| [`05_speech.py`](05_speech.py) | Speech-to-text | Parakeet CTC 1.1b | 3 | transcription | ⚠ needs function-id |
| [`06_parse.py`](06_parse.py) | Doc parsing | nemotron-parse | 1* | PDF/image → structured text | ✅ tested |

✅ tested = ran live against the API. **⚠ 05_speech** needs one value only you can fetch:
Parakeet's gRPC `function-id` (a UUID hiding on the JS-rendered model page) — paste it into
`nim.py`. Every slug/path is a named constant there, so when NVIDIA retires one (it happens),
the fix is one line.

`1*` = Shape 1, but the parse model takes the image **only** (it rejects a text prompt) and
returns a `markdown_bbox` tool call — a list of pages → elements `{bbox, text, type}` — not
plain `message.content`. `parse_document()` handles that for you.

## 🖼️ Multi-turn chat & image captioning

The headline feature for downstream projects. [`nim.ChatSession`](nim.py) gives you multi-turn
chat with image attach; [`chat.py`](chat.py) is an ollama-style REPL on top of it; and
`nim.VISION_CAPABLE` lists the models that actually accept images (**the API won't tell you** —
there's no capability field, so it's a curated list).

```python
import nim
s = nim.ChatSession(model="google/gemma-4-31b-it")
print(s.say("Caption this in one sentence.", images=["photo.png"]))
print(s.say("Now give me three hashtags."))   # remembers the image
```

Full wiring guide, batch-captioning pattern, and the "which model is fast enough" table live in
**[docs/multimodal.md](docs/multimodal.md)**.

## 🔎 Finding current model slugs (when a call 410s)

Slugs get retired. Two ways to see what's live right now:

**Interactive menu** — pick a modality → a model → it prints a ready-to-paste `nim.*` call:

    python menu.py

Arrow keys + type-to-filter in a real Windows console (PowerShell / cmd / Windows Terminal);
auto-falls-back to a numbered list in Git Bash or piped stdin. Chat (~105 models) adds an
**"era" step** — 2026+ / 2025 / pre-2025 / specialty — so you're not staring at the full wall.
(The API has no release dates either — `created` is a frozen constant — so years are
hand-assigned in `_CHAT_YEAR`; unknown slugs default to newest, so new models auto-surface.)

**Programmatic:**

    python -c "import nim; [print(m['id']) for m in nim.list_models('vision')]"

`/v1/models` exposes ~121 models but is **Shape 1 only** — rerank + image-gen (Shape 2) and
speech (Shape 3) aren't discoverable through any list endpoint, so `nim.py` keeps them in
`CURATED_MODELS`.

## 🧭 For agents working in this repo

Start at **[onboarding.md](onboarding.md)** — the map of what's here, how the three shapes work,
and the gotchas the API won't tell you (no dates, no capability flags, slugs churn).

## 🔭 The catalog goes deeper — good "next demo" candidates

- ✅ **Nemotron Parse** — shipped as `06_parse.py`.
- **BioNeMo** — protein folding / molecule generation. Pure tinkerer bait.
- **Canary** — multilingual ASR + speech translation (25 languages).
- **TTS (Magpie/FastPitch)** — the speech round-trip partner to Parakeet.
- **Nemotron VL / OCR** — document and scene-text understanding.

---

*Free tier, no affiliation with NVIDIA. Slugs and signup flows drift; this README is a
snapshot, the code constants are the source of truth.*
