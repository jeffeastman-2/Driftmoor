"""Tests for the LLM bridge factory (make_call_llm)."""

import asyncio
import json
import os
import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from engine.llm_bridge import make_call_llm, PROVIDER_CONFIGS


class TestProviderConfigs:
    def test_has_all_providers(self):
        expected = {"anthropic", "openai", "xai", "gemini", "deepseek", "ollama"}
        assert expected == set(PROVIDER_CONFIGS.keys())

    def test_each_has_agent_class(self):
        for name, cfg in PROVIDER_CONFIGS.items():
            assert "agent_class" in cfg, f"{name} missing agent_class"

    def test_each_has_env_var(self):
        for name, cfg in PROVIDER_CONFIGS.items():
            # ollama has no api key
            if name != "ollama":
                assert "env_var" in cfg, f"{name} missing env_var"


class TestMakeCallLLM:
    def test_returns_callable(self):
        fn = make_call_llm("xai", "grok-3", api_key="test-key")
        assert callable(fn)

    def test_returns_async_callable(self):
        fn = make_call_llm("xai", "grok-3", api_key="test-key")
        assert asyncio.iscoroutinefunction(fn)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            make_call_llm("unknown_provider", "model")

    def test_missing_api_key_raises(self):
        """Non-ollama providers require an API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError, match="API key"):
                make_call_llm("xai", "grok-3")  # no key, no env var

    def test_ollama_no_key_required(self):
        fn = make_call_llm("ollama", "qwen3:14b")
        assert callable(fn)


class TestCallLLMExecution:
    """Test that the callable correctly creates an agent and calls send_message."""

    def test_passes_system_and_user_to_agent(self):
        """The factory should create a fresh agent per call with system_prompt."""
        call_log = []

        # Mock agent class
        class MockAgent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                call_log.append(("init", kwargs))

            async def send_message(self, message, session):
                call_log.append(("send", message))
                return '{"intent": "test"}'

        with patch.dict("engine.llm_bridge.PROVIDER_CONFIGS", {
            "mock": {"agent_class": MockAgent},
        }):
            fn = make_call_llm("mock", "mock-model", api_key="key")
            result = asyncio.run(fn("system prompt here", "user message here"))

        # Agent was created with system_prompt
        assert call_log[0][0] == "init"
        assert call_log[0][1]["system_prompt"] == "system prompt here"
        assert call_log[0][1]["model"] == "mock-model"

        # send_message was called with user message
        assert call_log[1] == ("send", "user message here")
        assert result == '{"intent": "test"}'

    def test_fresh_agent_per_call(self):
        """Each call should create a new agent (no conversation history leaking)."""
        init_count = 0

        class MockAgent:
            def __init__(self, **kwargs):
                nonlocal init_count
                init_count += 1

            async def send_message(self, message, session):
                return "ok"

        with patch.dict("engine.llm_bridge.PROVIDER_CONFIGS", {
            "mock": {"agent_class": MockAgent},
        }):
            fn = make_call_llm("mock", "mock-model", api_key="key")
            asyncio.run(fn("sys1", "user1"))
            asyncio.run(fn("sys2", "user2"))

        assert init_count == 2

    def test_api_key_passed_to_agent(self):
        """API key should be passed to the agent constructor."""
        captured = {}

        class MockAgent:
            def __init__(self, **kwargs):
                captured.update(kwargs)

            async def send_message(self, message, session):
                return "ok"

        with patch.dict("engine.llm_bridge.PROVIDER_CONFIGS", {
            "mock": {"agent_class": MockAgent},
        }):
            fn = make_call_llm("mock", "mock-model", api_key="secret-123")
            asyncio.run(fn("sys", "usr"))

        assert captured["api_key"] == "secret-123"

    def test_ollama_no_api_key_in_kwargs(self):
        """Ollama agents should not receive api_key."""
        captured = {}

        class MockAgent:
            def __init__(self, **kwargs):
                captured.update(kwargs)

            async def send_message(self, message, session):
                return "ok"

        with patch.dict("engine.llm_bridge.PROVIDER_CONFIGS", {
            "ollama": {"agent_class": MockAgent},
        }):
            fn = make_call_llm("ollama", "qwen3:14b")
            asyncio.run(fn("sys", "usr"))

        assert "api_key" not in captured


class TestCallDelay:
    def test_call_delay_adds_pause(self):
        """call_delay should add a pause after each successful call."""
        class MockAgent:
            def __init__(self, **kwargs):
                pass

            async def send_message(self, message, session):
                return "ok"

        with patch.dict("engine.llm_bridge.PROVIDER_CONFIGS", {
            "ollama": {"agent_class": MockAgent},
        }):
            fn = make_call_llm("ollama", "test", call_delay=0.3)
            start = time.monotonic()
            asyncio.run(fn("sys", "usr"))
            elapsed = time.monotonic() - start
            assert elapsed >= 0.25  # should have waited ~0.3s

    def test_no_delay_by_default(self):
        """Without call_delay, calls return immediately."""
        class MockAgent:
            def __init__(self, **kwargs):
                pass

            async def send_message(self, message, session):
                return "ok"

        with patch.dict("engine.llm_bridge.PROVIDER_CONFIGS", {
            "ollama": {"agent_class": MockAgent},
        }):
            fn = make_call_llm("ollama", "test")
            start = time.monotonic()
            asyncio.run(fn("sys", "usr"))
            elapsed = time.monotonic() - start
            assert elapsed < 0.2
