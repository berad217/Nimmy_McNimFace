# Onboarding — Nimmy_McNimFace

A small reference kit for calling NVIDIA's NIM catalog (build.nvidia.com) — one free
`nvapi-` key, 120+ models across chat / vision / image / speech / embeddings / rerank /
doc-parse. Every call is wrapped in [`nim.py`](nim.py) so demos and downstream projects
stay tiny. This is the toolkit other projects (e.g. caption_lab) import for NIM access.

**Project type:** personal / hobby, public on GitHub (`berad217/Nimmy_McNimFace`)
**Human's level:** experienced (medical → EE → software)
**Current phase:** graduated out of The_Lab 2026-06-30; working kit, maintenance + new demos

---

## Getting oriented

- **[README.md](README.md)** — human-facing. The model, the three call shapes, the demos,
  and the **NVIDIA-key obstacle course** (how to actually get a key — there are many hoops).
- **[docs/multimodal.md](docs/multimodal.md)** — the deep guide: multi-turn chat, image
  captioning, batch patterns, model speed table, gotchas. Read this before wiring NIM vision
  into another project.
- **[docs/DEVLOG.md](docs/DEVLOG.md)** — what was built and why; append a dated entry per
  meaningful session.
- **[docs/.agents/current-handover.md](docs/.agents/current-handover.md)** — ephemeral delta:
  what's in-flight or unverified right now. Read in full (it's short); keep it lean.
- **[TASKS.md](TASKS.md)** — Active / Someday / Done queue. The Active list is the forward plan.
- **[nim.py](nim.py)** — the whole library. Read its module docstring first; every model
  slug and REST path is a named constant, so churn is a one-line fix.

This repo is **self-contained** — it does not depend on The_Lab's docs or memory. A session
started here as cwd has everything it needs in these files (plus Brad's user-global CLAUDE.md).

**Personal style for this human** lives in his global Claude memory
(`C:\Users\Brad\.claude\CLAUDE.md`): systems/first-principles thinker, wants direct feedback
over sugar-coating, decisive defaults over question rounds, Teflon mode (propose the next move).

---

## Repo layout

```
nim.py            the library -- all 3 call shapes + discovery (list_models, VISION_CAPABLE,
                  CURATED_MODELS, ChatSession). Demos & other projects import from here.
menu.py           interactive model picker over the live catalog (era buckets for chat,
                  numbered fallback when there's no real console)
chat.py           ollama-style multi-turn chat / captioning REPL
01_chat.py .. 06_parse.py   one minimal demo per modality
docs/multimodal.md          captioning / multi-turn wiring guide
docs/DEVLOG.md              build history
.env.example      copy to .env, paste nvapi- key   (.env is gitignored -- never commit it)
requirements.txt  openai, requests, python-dotenv, pillow, questionary
```

## The mental model: one key, three call shapes

| Shape | Transport | Modalities | Endpoint |
|---|---|---|---|
| 1 | `openai` SDK | chat, vision, embeddings, doc-parse | `integrate.api.nvidia.com/v1` |
| 2 | `requests` (REST) | reranking, image generation | `ai.api.nvidia.com/v1/...` |
| 3 | `nvidia-riva-client` (gRPC) | speech / ASR | `grpc.nvcf.nvidia.com:443` |

## Three things the API will NOT tell you (so we work around them)

1. **No release dates** — `GET /v1/models`'s `created` field is a frozen constant. `menu.py`
   hand-assigns years in `_CHAT_YEAR`; unknown slugs default to the newest bucket.
2. **No capability metadata** — nothing says a model accepts images. `nim.VISION_CAPABLE` is a
   curated list from the model pages.
3. **Only Shape 1 is discoverable** — `/v1/models` omits rerank/image (Shape 2) and speech
   (Shape 3) entirely; those live in `nim.CURATED_MODELS`.

## Reproduce / verify

```bash
pip install -r requirements.txt
cp .env.example .env          # paste nvapi- key (README has the how-to-get-one ordeal)
python 01_chat.py             # smoke test: prints a model reply
python menu.py                # browse the live catalog
```

`05_speech.py` is the only demo not green out of the box: it needs Parakeet's gRPC
`function-id` (a UUID on the JS-rendered model page) pasted into `nim.py`.

## About this human

See `C:\Users\Brad\.claude\CLAUDE.md`. Short version: explain jargon outside bio/EE/code,
challenge bad ideas directly, keep "done" crisp (he's prone to mission creep), and after a
task propose the next concrete move rather than asking "what now?".
