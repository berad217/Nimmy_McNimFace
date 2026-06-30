"""Tiny multi-turn chat REPL over NIM (ollama-style), with image attach for captioning.

A plain input() loop -- no console/TTY quirks, works in any shell. Replies stream as
they arrive. Built on nim.ChatSession, so it's the same machinery you'd import into
caption_lab or anywhere else.

Usage:
    python chat.py                              # default vision model, text or image chat
    python chat.py qwen/qwen3.5-122b-a10b       # pick a model (full slug)
    python chat.py google/gemma-4-31b-it cat.png  # start with an image attached

In-REPL commands:
    /image <path>   attach an image to your NEXT message (vision models only)
    /model <slug>   switch model, keeping the conversation
    /reset          clear the conversation
    /models         list vision-capable model slugs (good for captioning)
    /exit           quit  (also Ctrl-C / Ctrl-D / blank line)
"""

from __future__ import annotations

import os
import sys

import nim

DEFAULT_MODEL = "google/gemma-4-31b-it"  # vision-capable and reasonably fast


def main() -> int:
    argv = sys.argv[1:]
    model = argv[0] if argv else DEFAULT_MODEL
    session = nim.ChatSession(model=model)
    pending: list[str] = []  # image paths queued for the next message

    if len(argv) > 1:  # optional starting image
        pending.append(argv[1])

    print(f"NIM chat -- model: {model}")
    print("Type a message, or /image <path> to attach an image. /exit to quit.\n")

    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            return 0
        if line in ("/exit", "/quit"):
            return 0
        if line == "/reset":
            session.reset()
            pending.clear()
            print("(conversation cleared)\n")
            continue
        if line == "/models":
            for m in nim.VISION_CAPABLE:
                print("  ", m)
            print()
            continue
        if line.startswith("/model "):
            session.model = line[len("/model "):].strip()
            print(f"(model -> {session.model})\n")
            continue
        if line.startswith("/image "):
            path = line[len("/image "):].strip().strip('"')
            if os.path.isfile(path):
                pending.append(path)
                print(f"(attached {path}; send a message to caption it)\n")
            else:
                print(f"(no such file: {path})\n")
            continue

        # A normal message -> stream the reply, consuming any queued images.
        print("bot> ", end="", flush=True)
        try:
            session.say(line, images=pending or None, stream=True)
        except Exception as exc:  # noqa: BLE001 -- keep the REPL alive on API errors
            print(f"\n(error: {exc})")
        else:
            pending.clear()
        print()


if __name__ == "__main__":
    raise SystemExit(main())
