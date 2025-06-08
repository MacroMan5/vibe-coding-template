"""Environment configuration utilities for VIBE Core."""

from __future__ import annotations

import logging
import os
from typing import Tuple

from dotenv import load_dotenv


def load_api_keys() -> Tuple[str, str]:
    """Load API keys from .env into environment and return them.
    
    Returns:
        Tuple of (openai_key, anthropic_key)
        
    Raises:
        ValueError: If required API keys are missing
    """
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not openai_key:
        raise ValueError("Missing OPENAI_API_KEY in environment")
    logging.info("OpenAI key loaded")

    if not anthropic_key:
        raise ValueError("Missing ANTHROPIC_API_KEY in environment")
    logging.info("Anthropic key loaded")

    return openai_key, anthropic_key
