"""Groq connection and reusable prompt helper."""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass


def ask_llm(prompt: str, *, model: str = "openai/gpt-oss-20b") -> str:
    """Send a prompt to Groq and return the generated text."""
    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Set GROQ_API_KEY before calling the Groq API.")

    response = Groq(api_key=api_key).chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(ask_llm("What is a spare part?"))
