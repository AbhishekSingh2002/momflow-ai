"""
app/config.py — Provider configuration and model selection.

Supports OpenAI and OpenRouter providers with fallback handling.
"""

import os
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

Provider = Literal["openai", "openrouter"]

# ── Provider Configuration ──────────────────────────────────────────────────

MODEL_PROVIDER: Provider = os.getenv("MODEL_PROVIDER", "openai").lower()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1"

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── Model Selection ────────────────────────────────────────────────────────

EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "gpt-4o-mini")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gpt-4o-mini")
TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
STT_MODEL = os.getenv("STT_MODEL", "whisper-1")

# ── Provider Detection ─────────────────────────────────────────────────────

def get_provider_config() -> dict:
    """
    Returns the appropriate provider configuration based on environment settings.
    """
    if MODEL_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY required when MODEL_PROVIDER=openrouter")
        
        return {
            "provider": "openrouter",
            "api_key": OPENROUTER_API_KEY,
            "base_url": OPENROUTER_BASE_URL,
            "extraction_model": EXTRACTION_MODEL,
        }
    
    else:  # Default to OpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required for OpenAI provider")
        
        return {
            "provider": "openai",
            "api_key": OPENAI_API_KEY,
            "base_url": OPENAI_BASE_URL,
            "extraction_model": EXTRACTION_MODEL,
            "tts_model": TTS_MODEL,
            "stt_model": STT_MODEL,
        }

def get_openai_client():
    """Get OpenAI client with appropriate configuration."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("OpenAI package required. Install with: pip install openai")
    
    config = get_provider_config()
    
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )

# Create the STT client instance for import (always uses OpenAI)
try:
    from openai import OpenAI
except ImportError:
    raise ImportError("OpenAI package required. Install with: pip install openai")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY required for speech-to-text")

stt_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# Create the LLM client instance for import
llm_client = get_openai_client()

# Check if the provider supports JSON object mode
SUPPORTS_JSON_OBJECT = MODEL_PROVIDER == "openai"  # OpenRouter may not support json_object mode

# ── Validation ─────────────────────────────────────────────────────────────

def validate_config() -> list[str]:
    """Validate configuration and return list of issues."""
    issues = []
    
    if MODEL_PROVIDER not in ["openai", "openrouter"]:
        issues.append(f"Invalid MODEL_PROVIDER: {MODEL_PROVIDER}")
    
    if MODEL_PROVIDER == "openai" and not OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY required for OpenAI provider")
    
    if MODEL_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
        issues.append("OPENROUTER_API_KEY required for OpenRouter provider")
    
    return issues

# ── Debug Info ────────────────────────────────────────────────────────────

def print_config():
    """Print current configuration for debugging."""
    config = get_provider_config()
    
    print(f"Provider: {config['provider']}")
    print(f"Base URL: {config['base_url']}")
    print(f"Extraction Model: {config['extraction_model']}")
    
    if config['provider'] == 'openai':
        print(f"TTS Model: {config.get('tts_model', 'N/A')}")
        print(f"STT Model: {config.get('stt_model', 'N/A')}")

if __name__ == "__main__":
    # Validate and print config
    issues = validate_config()
    if issues:
        print("Configuration issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration valid:")
        print_config()
