"""Demo 3 -- Tiny RAG: embed -> shortlist by cosine -> rerank for precision.

Shows the embed+rerank pair that makes retrieval actually good (shapes 1 + 2).
Maps to: social_dynamics_kb.
Run: python 03_rag.py
"""

import math

from nim import embed, rerank

DOCS = [
    "The LPU is Groq's custom inference chip.",
    "Cerebras builds wafer-scale engines the size of a dinner plate.",
    "Parakeet is NVIDIA's family of fast ASR models.",
    "FLUX is a text-to-image model from Black Forest Labs.",
]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb)


if __name__ == "__main__":
    query = "What chip does Cerebras make?"

    # 1) cheap recall: embed query + docs, rank by cosine similarity
    qv = embed([query], input_type="query")[0]
    dvs = embed(DOCS, input_type="passage")
    ranked = sorted(range(len(DOCS)), key=lambda i: cosine(qv, dvs[i]), reverse=True)
    print("Top-3 by embedding:")
    for i in ranked[:3]:
        print(f"  - {DOCS[i]}")

    # 2) precision: rerank the shortlist with a cross-encoder
    shortlist = [DOCS[i] for i in ranked[:3]]
    order = rerank(query, shortlist)
    print(f"\nBest after rerank: {shortlist[order[0][0]]}")
