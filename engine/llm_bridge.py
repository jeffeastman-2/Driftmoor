"""Bridge between engine/agents/ wrappers and the CallLLM interface.

The role modules (PlayerLeft, PlayerRight, DMLeft, DMRight) expect:
    call_llm: async (system_prompt: str, user_message: str) -> str

The existing agent wrappers take system_prompt at construction time
and user_message at send_message() time.

make_call_llm() bridges these: it returns a CallLLM callable that
creates a fresh agent per call (no conversation history leaking).
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

import aiohttp

from engine.agents import (
    ClaudeAgent, ChatGPTAgent, GrokAgent, OllamaAgent, GeminiAgent, DeepSeekAgent,
)

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

PROVIDER_CONFIGS = {
    "anthropic": {
        "agent_class": ClaudeAgent,
        "env_var": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "agent_class": ChatGPTAgent,
        "env_var": "OPENAI_API_KEY",
    },
    "xai": {
        "agent_class": GrokAgent,
        "env_var": "XAI_API_KEY",
    },
    "gemini": {
        "agent_class": GeminiAgent,
        "env_var": "GOOGLE_API_KEY",
    },
    "deepseek": {
        "agent_class": DeepSeekAgent,
        "env_var": "DEEPSEEK_API_KEY",
    },
    "ollama": {
        "agent_class": OllamaAgent,
    },
}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_call_llm(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    call_delay: float = 0.0,
) -> "CallLLM":
    """Create a CallLLM callable for the given provider and model.

    Args:
        provider: One of "anthropic", "openai", "xai", "gemini",
                  "deepseek", "ollama".
        model:    Model name (e.g. "grok-3", "gpt-4o", "qwen3:14b").
        api_key:  API key. If None, read from the provider's env var.
                  Not needed for ollama.
        call_delay: Seconds to wait after each successful call.
                  Helps avoid rate-limiting on busy providers.

    Returns:
        An async callable: (system_prompt, user_message) -> str

    Raises:
        ValueError:        Unknown provider.
        EnvironmentError:  API key required but not found.
    """
    if provider not in PROVIDER_CONFIGS:
        raise ValueError(f"Unknown provider: {provider}")

    cfg = PROVIDER_CONFIGS[provider]
    agent_class = cfg["agent_class"]

    # Resolve API key
    resolved_key = api_key
    if provider != "ollama" and resolved_key is None:
        env_var = cfg.get("env_var", "")
        resolved_key = os.environ.get(env_var, "")
        if not resolved_key:
            raise EnvironmentError(
                f"API key required for {provider}. "
                f"Set {env_var} or pass api_key=."
            )

    async def _call(system_prompt: str, user_message: str) -> str:
        # Fresh agent per call — no conversation history leaking
        kwargs = {
            "name": f"{provider}_role",
            "model": model,
            "system_prompt": system_prompt,
        }
        if provider != "ollama":
            kwargs["api_key"] = resolved_key

        # Retry with capped exponential backoff for transient errors (503, 429, 529).
        # Backoff: 2s, 4s, 8s, 16s, 32s, then one final attempt after 60s.
        # If the call still fails after that 60s wait, we give up and raise.
        MAX_WAIT = 60
        attempt = 0
        hit_max_wait = False
        while True:
            agent = agent_class(**kwargs)
            try:
                async with aiohttp.ClientSession() as session:
                    result = await agent.send_message(user_message, session)
                    if call_delay > 0:
                        await asyncio.sleep(call_delay)
                    return result
            except Exception as e:
                error_str = str(e)
                retryable = any(code in error_str for code in ("503", "429", "529"))
                if retryable and not hit_max_wait:
                    wait = min(2 ** (attempt + 1), MAX_WAIT)  # 2, 4, 8, 16, 32, 60
                    attempt += 1
                    if wait >= MAX_WAIT:
                        hit_max_wait = True  # this is the last attempt
                    print(f"  [{provider}] {error_str[:60]}... retry {attempt} in {wait}s")
                    await asyncio.sleep(wait)
                    continue
                raise

    return _call
