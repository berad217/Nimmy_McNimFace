"""Demo 1 -- LLM chat (OpenAI-compatible shape).

Maps to: book_generator, quazy-quizzer, swarm_api_interface.
Run: python 01_chat.py
"""

from nim import chat

if __name__ == "__main__":
    print("Model: meta/llama-3.3-70b-instruct  "
          "(swap to deepseek-ai/deepseek-r1 for a reasoning model)\n")
    chat("In 3 sentences, explain why wafer-scale chips are fast at inference.",
         stream=True)
