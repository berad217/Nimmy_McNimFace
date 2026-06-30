# Multimodal chat & image captioning on NIM

Reference for wiring NVIDIA NIM vision-language models into other projects
(e.g. `caption_lab`). Companion code: `nim.py` (`ChatSession`, `describe_image`,
`VISION_CAPABLE`) and `chat.py` (interactive REPL).

## TL;DR

It's easy. Image input rides the **same OpenAI-compatible endpoint** as text chat
(`integrate.api.nvidia.com/v1`, Shape 1) — no separate API, no extra dependency beyond
the `openai` SDK you already have. An image is just a content block in a user message.
Captioning works against the modern multimodal models out of the box; multi-turn is just
keeping the `messages` list around.

## The one fact to internalize

A user message's `content` can be a **list of typed blocks** instead of a string:

```python
content = [
    {"type": "text", "text": "Caption this image."},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,<...>"}},
]
```

Images are passed inline as **base64 data URLs** (NVIDIA's hosted endpoint accepts that;
`nim._data_url(path)` builds one with the right MIME type). You can put multiple image
blocks in one message. That's the whole trick.

## Which models accept images

**The API does not tell you.** `GET /v1/models` has no capability metadata — a model's
modality only lives on its page at build.nvidia.com. So image-capability is a curated
list: `nim.VISION_CAPABLE`. Keep it current by hand.

Two families accept images:

| Kind | Examples | Notes |
|---|---|---|
| Modern multimodal chat | `google/gemma-4-31b-it`, `qwen/qwen3.5-122b-a10b`, `mistralai/mistral-small-4-119b-2603`, `moonshotai/kimi-k2.6`, `minimaxai/minimax-m3`, `stepfun-ai/step-3.7-flash`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Text-first models that also read images (some also video/audio). These are the good captioners. |
| Dedicated vision-language | `meta/llama-3.2-11b-vision-instruct`, `meta/llama-3.2-90b-vision-instruct`, `microsoft/phi-4-multimodal-instruct`, `nvidia/nemotron-nano-12b-v2-vl`, `adept/fuyu-8b` | Older / purpose-built VLMs. |

> The `menu.py` "vision" tab is driven by `nim.VISION_CAPABLE`, so it lists both the
> dedicated VLMs and the modern multimodal chat models (gemma-4, qwen3.5, ...). Those
> also still appear under **chat** (image input is a capability, not an exclusive
> category) -- vision is just the cross-cutting "accepts images" view.

## Recipes

### 1. Single image -> caption (one shot)

```python
import nim
caption = nim.describe_image("photo.png", "Write a one-sentence caption.",
                             model="google/gemma-4-31b-it")
```

### 2. Multi-turn: caption, then follow up

```python
s = nim.ChatSession(model="google/gemma-4-31b-it")
print(s.say("Caption this in one sentence.", images=["photo.png"]))
print(s.say("Now give me three Instagram hashtags."))   # remembers the image
```

The model sees the full history, so later turns can reference an image attached earlier.

### 3. Interactive REPL

```
python chat.py google/gemma-4-31b-it photo.png
```

Then chat; `/image <path>` attaches another image, `/models` lists captioners, `/exit` quits.

### 4. Batch captioning (the caption_lab pattern)

For many images, use a **fresh call per image** — don't accumulate them in one session
(see the token gotcha below). A plain loop:

```python
import nim
def caption_all(paths, model="google/gemma-4-31b-it", prompt="Caption in one sentence."):
    return {p: nim.describe_image(p, prompt, model=model) for p in paths}
```

To go faster, run several concurrently (NIM allows ~40 req/min on the free key):

```python
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as ex:
    captions = dict(zip(paths, ex.map(
        lambda p: nim.describe_image(p, prompt, model=model), paths)))
```

## Gotchas

- **Model speed varies wildly.** Measured on one 1024px image, one-sentence caption:
  `mistral-small-4` ~1.7s, `gemma-4-31b` ~13s, `qwen3.5-122b` ~**94s** (it's a *reasoning*
  model — it "thinks" before answering). For batch work this dominates everything; pick a
  fast model unless you need the quality. `gemma-4-31b-it` is a good default.
- **Images are re-sent every turn.** The endpoint is stateless, so a `ChatSession` resends
  all prior images on each call — input-token cost grows with history. For batch captioning,
  one fresh call (or fresh session) per image is cheaper than one long session.
- **Image vs video/audio are different calls.** `image_url` blocks cover *images* only.
  Models that list video/audio need different content types (or a different endpoint); this
  doc and `nim.py` cover images.
- **Rate limit:** ~40 requests/min on the free `nvapi-` key. Cap concurrency accordingly.
- **No capability metadata** in the API (see above) — `VISION_CAPABLE` is hand-curated and
  can drift as the catalog changes.

## Wiring into caption_lab

1. Copy or import `nim.py` (it's dependency-light: `openai`, `requests`, `python-dotenv`).
2. Set `NVIDIA_API_KEY` (see `.env.example`).
3. Pick a model from `nim.VISION_CAPABLE` — default `google/gemma-4-31b-it` for speed/quality.
4. Single image -> `nim.describe_image`; conversational -> `nim.ChatSession`; batch -> the
   loop in recipe 4.
