"""Demo 5 -- Speech-to-text with Parakeet (gRPC / Riva shape).

Maps to: parakeet, eighty-eight-D.
Setup: pip install nvidia-riva-client  AND set PARAKEET_FUNCTION_ID in nim.py
       (build.nvidia.com -> parakeet model -> API tab -> function-id).
Audio must be 16-bit mono WAV.
Run: python 05_speech.py clip.wav
"""

import sys

from nim import transcribe

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "clip.wav"
    print(transcribe(path))
