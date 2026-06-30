"""Shared helpers for the NVIDIA NIM demo collection.

One nvapi- key (set NVIDIA_API_KEY) unlocks every model on build.nvidia.com.
The catch: there are THREE call shapes behind that one key --

  1. OpenAI-compatible -> chat, vision (VLM), embeddings, doc-parse  (integrate.api.nvidia.com/v1)
  2. Plain REST        -> reranking, image generation                (ai.api.nvidia.com/v1/...)
  3. gRPC (Riva)       -> speech / ASR (Parakeet, Canary)            (grpc.nvcf.nvidia.com:443)

Each demo imports from here so it can stay tiny. Model slugs and REST paths churn:
every one is a clearly-named argument/constant; if a call 410s/404s, get the current
value from `list_models()` below (live `GET /v1/models`), the `menu.py` picker, or the
model's page on build.nvidia.com.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os

import requests

try:  # auto-load .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

OPENAI_BASE = "https://integrate.api.nvidia.com/v1"
REST_BASE = "https://ai.api.nvidia.com/v1"


def key() -> str:
    """Return the NVIDIA API key, or raise a clear error if it is unset."""
    k = os.environ.get("NVIDIA_API_KEY")
    if not k:
        raise RuntimeError(
            "set NVIDIA_API_KEY (see .env.example); get one free at build.nvidia.com"
        )
    return k


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {key()}", "Accept": "application/json"}


def _data_url(image_path: str) -> str:
    """Inline an image as a base64 data URL, with the right MIME from its extension."""
    mime = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


# --- Discovery: what's live right now -------------------------------------------

# Slug fragments that flag a non-chat modality. Checked in order, so 'embed' wins
# over 'vision' for the VLM-embedding models that match both (e.g. ...vlm-embed...).
_MODALITY_HINTS = (
    ("embedding", ("embed", "bge-", "embedqa")),
    ("vision", ("vision", "-vlm", "fuyu", "deplot", "phi-3-vision")),
)

# Shapes 2 & 3 are NOT in GET /v1/models -- nothing lists them. Curate them here so a
# menu has one source of truth. Update slugs/function-id from build.nvidia.com if they churn.
CURATED_MODELS = [
    {"id": "nvidia/llama-nemotron-rerank-1b-v2", "modality": "rerank", "shape": "rest"},
    {"id": "black-forest-labs/flux.1-dev",       "modality": "image",  "shape": "rest"},
    {"id": "nvidia/parakeet-ctc-1.1b-asr",       "modality": "speech", "shape": "grpc"},
]

# Models that ACCEPT IMAGE INPUT (for captioning / visual Q&A). The API exposes no
# capability metadata -- /v1/models won't tell you a model is multimodal -- so this is a
# hand-curated list from NVIDIA's model pages. Most are general chat models that also take
# images; a few are dedicated vision-language models. Add to it as the catalog grows.
VISION_CAPABLE = [
    # Modern multimodal chat (text + image, some also video/audio):
    "google/gemma-4-31b-it",
    "minimaxai/minimax-m3",
    "mistralai/mistral-small-4-119b-2603",
    "moonshotai/kimi-k2.6",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "qwen/qwen3.5-122b-a10b",
    "qwen/qwen3.5-397b-a17b",
    "stepfun-ai/step-3.7-flash",
    # Dedicated / classic vision-language models:
    "meta/llama-3.2-11b-vision-instruct",
    "meta/llama-3.2-90b-vision-instruct",
    "microsoft/phi-3-vision-128k-instruct",
    "microsoft/phi-4-multimodal-instruct",
    "nvidia/nemotron-nano-12b-v2-vl",
    "nvidia/llama-3.1-nemotron-nano-vl-8b-v1",
    "adept/fuyu-8b",
]


def _infer_modality(model_id: str) -> str:
    """Guess a model's modality from its slug (the API doesn't report one)."""
    low = model_id.lower()
    for modality, fragments in _MODALITY_HINTS:
        if any(f in low for f in fragments):
            return modality
    return "chat"


def list_models(modality: str | None = None) -> list[dict]:
    """List the live Shape-1 catalog (chat / vision / embedding) for menus or slug recovery.

    Live-pulled from GET /v1/models, so it always reflects the current offerings -- use it to
    populate a menu, or to find the right slug when a hardcoded one 404s. Each record is
    {id, owned_by, modality}, sorted by (owned_by, id). `modality` is INFERRED from the slug
    ('chat'/'vision'/'embedding'); pass modality= to filter to one.

    Only sees Shape 1. Reranking + image-gen (Shape 2) and speech (Shape 3) are not
    discoverable through any endpoint -- see CURATED_MODELS for those.
    """
    r = requests.get(f"{OPENAI_BASE}/models", headers=_headers(), timeout=30)
    r.raise_for_status()
    models = [
        {"id": m["id"], "owned_by": m.get("owned_by", ""),
         "modality": _infer_modality(m["id"])}
        for m in r.json()["data"]
    ]
    if modality:
        models = [m for m in models if m["modality"] == modality]
    return sorted(models, key=lambda m: (m["owned_by"], m["id"]))


# --- Shape 1: OpenAI-compatible (chat / vision / embeddings / doc-parse) ---------

def _client():
    from openai import OpenAI

    return OpenAI(base_url=OPENAI_BASE, api_key=key())


def chat(prompt: str, model: str = "meta/llama-3.3-70b-instruct",
         stream: bool = False, **kwargs) -> str:
    """One-shot text chat.

    Swap `model` for any LLM slug on build.nvidia.com -- e.g.
    'deepseek-ai/deepseek-r1' or 'nvidia/llama-3.1-nemotron-70b-instruct'.
    """
    resp = _client().chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=stream,
        **kwargs,
    )
    if not stream:
        return resp.choices[0].message.content
    pieces: list[str] = []
    for chunk in resp:
        if not chunk.choices:  # NIM sends a final/usage chunk with no choices
            continue
        piece = chunk.choices[0].delta.content or ""
        print(piece, end="", flush=True)
        pieces.append(piece)
    print()
    return "".join(pieces)


def describe_image(image_path: str, prompt: str,
                   model: str = "meta/llama-3.2-11b-vision-instruct") -> str:
    """Vision-language: ask a question about a local image (base64-inlined)."""
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": _data_url(image_path)}},
    ]
    resp = _client().chat.completions.create(
        model=model, messages=[{"role": "user", "content": content}]
    )
    return resp.choices[0].message.content


class ChatSession:
    """Multi-turn chat against any OpenAI-compatible NIM model, with optional images.

    Holds the running `messages` list so each turn sees the full history. Attach local
    image paths to any user turn; a vision-capable model (see VISION_CAPABLE) will read
    them. Reusable across projects -- e.g. caption an image then ask follow-ups:

        s = nim.ChatSession(model="google/gemma-4-31b-it")
        print(s.say("Caption this in one sentence.", images=["photo.png"]))
        print(s.say("Now give me three hashtags."))   # still remembers the image

    NOTE: the endpoint is stateless, so every prior image is RE-SENT on each turn and
    keeps costing input tokens. For batch captioning of many images, prefer one fresh
    session (or just nim.describe_image) per image rather than one long session.
    """

    def __init__(self, model: str = "meta/llama-3.3-70b-instruct",
                 system: str | None = None) -> None:
        self.model = model
        self.messages: list[dict] = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def say(self, text: str, images: list[str] | None = None,
            stream: bool = False, **kwargs) -> str:
        """Send a user turn (optionally with images), append the reply, return its text.

        With stream=True the reply is printed token-by-token as it arrives (handy for a
        REPL) and the full string is still returned.
        """
        if images:  # multimodal turn -> list of typed content blocks
            content: list[dict] = [{"type": "text", "text": text}]
            content += [{"type": "image_url", "image_url": {"url": _data_url(p)}}
                        for p in images]
            self.messages.append({"role": "user", "content": content})
        else:        # plain text turn
            self.messages.append({"role": "user", "content": text})

        resp = _client().chat.completions.create(
            model=self.model, messages=self.messages, stream=stream, **kwargs)
        if not stream:
            reply = resp.choices[0].message.content
        else:
            pieces: list[str] = []
            for chunk in resp:
                if not chunk.choices:  # NIM sends a final/usage chunk with no choices
                    continue
                piece = chunk.choices[0].delta.content or ""
                print(piece, end="", flush=True)
                pieces.append(piece)
            print()
            reply = "".join(pieces)

        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        """Drop the conversation, keeping the system prompt if one was set."""
        keep_system = self.messages and self.messages[0]["role"] == "system"
        self.messages = self.messages[:1] if keep_system else []


def parse_document(image_path: str, model: str = "nvidia/nemotron-parse") -> list[dict]:
    """Parse a document-page IMAGE into structured elements.

    Nemotron Parse takes the image ONLY (no text prompt -- it rejects text input) and
    returns its result as a tool call named 'markdown_bbox': a list of pages, each a
    list of elements {bbox: {xmin,ymin,xmax,ymax} normalized, text, type} where type is
    Title/Text/Table/etc. Tables come back as LaTeX/markdown. Returns a flat element list.
    """
    resp = _client().chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": _data_url(image_path)}},
        ]}],
    )
    calls = resp.choices[0].message.tool_calls
    if not calls:
        raise RuntimeError("parse model returned no tool_calls (content: "
                           + repr(resp.choices[0].message.content) + ")")
    pages = json.loads(calls[0].function.arguments)
    return [element for page in pages for element in page]


def embed(texts: list[str], input_type: str = "passage",
          model: str = "nvidia/llama-nemotron-embed-1b-v2") -> list[list[float]]:
    """Embed text. Use input_type='query' for searches, 'passage' for documents."""
    resp = _client().embeddings.create(
        model=model,
        input=texts,
        extra_body={"input_type": input_type, "truncate": "END"},
    )
    return [d.embedding for d in resp.data]


# --- Shape 2: plain REST (reranking / image generation) -------------------------

def rerank(query: str, passages: list[str],
           model: str = "nvidia/llama-nemotron-rerank-1b-v2") -> list[tuple[int, float]]:
    """Rerank passages by relevance. Returns [(orig_index, score), ...] best-first.

    NOTE: if this 404s, confirm the path on the model's API page on build.nvidia.com.
    """
    url = f"{REST_BASE}/retrieval/nvidia/llama-nemotron-rerank-1b-v2/reranking"
    payload = {
        "model": model,
        "query": {"text": query},
        "passages": [{"text": p} for p in passages],
    }
    r = requests.post(url, headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return [(item["index"], item["logit"]) for item in r.json()["rankings"]]


def generate_image(prompt: str, out_path: str = "out.png",
                   model_path: str = "black-forest-labs/flux.1-dev", **params) -> str:
    """Text-to-image via FLUX. Saves a PNG, returns the path.

    Request/response confirmed against NVIDIA's visual-genai docs: the hosted
    endpoint returns the image inline (synchronous, no polling) under
    artifacts[0].base64. The OpenAI-style b64_json shape is handled as a fallback.
    """
    url = f"{REST_BASE}/genai/{model_path}"
    payload = {"prompt": prompt, "mode": "base", "width": 1024, "height": 1024,
               "steps": 50, "seed": 0, "cfg_scale": 3.5, **params}
    r = requests.post(url, headers=_headers(), json=payload, timeout=120)
    r.raise_for_status()
    body = r.json()
    if "artifacts" in body:        # FLUX / SDXL shape (confirmed in NIM docs)
        b64 = body["artifacts"][0]["base64"]
    elif "data" in body:           # OpenAI-image shape (response_format=b64_json)
        b64 = body["data"][0]["b64_json"]
    else:
        raise RuntimeError(f"unexpected image response keys: {list(body)}")
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64))
    return out_path


# --- Shape 3: gRPC / Riva (speech-to-text) --------------------------------------

# Parakeet runs over gRPC (Riva), so it needs a per-model NVCF function-id -- the one
# value that can't be fetched headlessly. Copy it from:
#   build.nvidia.com -> parakeet-ctc-1.1b-asr -> "API" tab -> the gRPC/python snippet's
#   "function-id" header (a UUID). Paste it below, or pass function_id=... to transcribe().
PARAKEET_FUNCTION_ID = "REPLACE_WITH_FUNCTION_ID"


def transcribe(wav_path: str, function_id: str = PARAKEET_FUNCTION_ID,
               language: str = "en-US") -> str:
    """Transcribe a 16-bit mono WAV with Parakeet via Riva gRPC.

    Requires `pip install nvidia-riva-client` and the model's function-id.
    """
    import riva.client  # lazy: only this demo needs the gRPC client

    auth = riva.client.Auth(
        uri="grpc.nvcf.nvidia.com:443",
        use_ssl=True,
        metadata_args=[["function-id", function_id],
                       ["authorization", f"Bearer {key()}"]],
    )
    asr = riva.client.ASRService(auth)
    with open(wav_path, "rb") as f:
        audio = f.read()
    config = riva.client.RecognitionConfig(language_code=language, max_alternatives=1)
    resp = asr.offline_recognize(audio, config)
    return " ".join(r.alternatives[0].transcript for r in resp.results)
