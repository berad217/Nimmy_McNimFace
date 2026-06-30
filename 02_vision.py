"""Demo 2 -- Vision-language model (OpenAI shape, image inlined as base64).

Maps to: panel_reader, camera-mccameraface, stereo-viewer.
Run: python 02_vision.py path/to/image.jpg
"""

import sys

from nim import describe_image

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample.jpg"
    answer = describe_image(path, "Describe this image. Read any text you can see.")
    print(answer)
