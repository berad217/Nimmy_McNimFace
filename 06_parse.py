"""Demo 6 -- Document parsing with Nemotron Parse (OpenAI shape, IMAGE-ONLY input).

Returns structured elements -- each with a semantic type (Title / Text / Table), the
text (tables come back as LaTeX/markdown), and a normalized bounding box. A strict
upgrade over plain text extraction. Maps to: PDF_embedded_text_extractor, panel_reader.

Run: python 06_parse.py [path/to/page.png]   (no arg -> renders a sample doc first)
"""

import sys

from nim import parse_document


def make_sample(path: str = "doc_sample.png") -> str:
    """Render a small document with a title, fields, and a table (known ground truth)."""
    from PIL import Image, ImageDraw, ImageFont

    def font(sz):
        try:
            return ImageFont.truetype("arial.ttf", sz)
        except Exception:
            return ImageFont.load_default()

    img = Image.new("RGB", (860, 560), "white")
    d = ImageDraw.Draw(img)
    d.text((40, 28), "Quarterly Lab Report", fill="black", font=font(34))
    d.text((40, 90), "Project: Hooky McHookface", fill="black", font=font(22))
    d.text((40, 122), "Status: webhook receiver rewrite in progress", fill="black", font=font(22))
    cols = [(40, "Metric"), (360, "Q1"), (560, "Q2")]
    rows = [("Webhooks/day", "120", "340"),
            ("p99 latency", "85 ms", "42 ms"),
            ("Uptime", "99.1%", "99.8%")]
    for x, h in cols:
        d.text((x, 200), h, fill="black", font=font(24))
    d.line((40, 235, 720, 235), fill="black", width=2)
    y = 250
    for r in rows:
        for (x, _), cell in zip(cols, r):
            d.text((x, y), cell, fill="black", font=font(22))
        y += 38
    img.save(path)
    return path


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else make_sample()
    elements = parse_document(path)
    print(f"Parsed {len(elements)} elements from {path}:\n")
    for e in elements:
        print(f"[{e['type']}]  bbox={tuple(round(v, 2) for v in e['bbox'].values())}")
        print(e["text"])
        print()
