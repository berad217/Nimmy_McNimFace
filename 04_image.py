"""Demo 4 -- Text-to-image with FLUX (plain REST shape).

Maps to: bananagen, spritey-mcspriteface, Sketchy_McSketchface.
Run: python 04_image.py "a low-poly biplane over green hills, game asset"
"""

import sys

from nim import generate_image

if __name__ == "__main__":
    prompt = (sys.argv[1] if len(sys.argv) > 1
              else "a friendly cartoon beaker mascot, sticker art, white background")
    path = generate_image(prompt, out_path="flux_out.png")
    print(f"Saved {path}")
