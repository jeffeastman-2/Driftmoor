#!/usr/bin/env python3
"""
Fey Glade Orchestrator — PHASE 2
Real OpenClaw sub-agent integration with configurable LLM selection.

Replaces mock responses with actual sub-agent spawning.
"""

import json
import sys
import os
import asyncio
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional
import re
import time

import aiohttp

# Import the Phase 1 orchestrator classes
from fey_glade_orchestrator import (
    NeurochemicalState,
    CharacterCondition,
    CharacterAction,
    SceneState,
    FeyGladeOrchestrator,
)
from engine.agents import (
    ClaudeAgent, ChatGPTAgent, GrokAgent, OllamaAgent, GeminiAgent, DeepSeekAgent,
)

# =========================================================================
# LLM CONFIGURATION
# =========================================================================

@dataclass
class LLMConfig:
    """Configuration for an LLM provider and model."""
    provider: str  # "anthropic", "openai", "ollama", etc.
    model: str     # "claude-sonnet-4-6", "gpt-4o", "qwen:14b", etc.
    
    def __str__(self) -> str:
        return f"{self.provider}/{self.model}"


@dataclass
class AgentConfig:
    """Configuration for a character agent."""
    character_id: str
    character_name: str
    llm: LLMConfig = field(default_factory=lambda: LLMConfig("anthropic", "claude-sonnet-4-6"))
    
    def __str__(self) -> str:
        return f"{self.character_name} ({self.llm})"


# =========================================================================
# PHASE 2: REAL SUB-AGENT ORCHESTRATOR
# =========================================================================

class FeyGladeOrchestratorPhase2(FeyGladeOrchestrator):
    """
    Extends Phase 1 orchestrator to spawn real OpenClaw sub-agents.
    
    Configuration:
      agent_configs: dict[str, AgentConfig]
        - Maps character_id → LLM config
        - Allows different models per character
        - Default: Sonnet for all
    
    Integration points:
      - sessions_spawn() to call sub-agents
      - Parse structured JSON response
      - Fallback to mock if spawn fails
    """

    def __init__(self, 
                 scenario_path: Path = Path("./scenario"),
                 runtime_path: Path = Path("./runtime"),
                 agent_configs: Optional[dict[str, AgentConfig]] = None,
                 use_real_agents: bool = True,
                 fallback_to_mock: bool = True):
        """
        Initialize Phase 2 orchestrator.
        
        Args:
            scenario_path: Path to scenario files
            runtime_path: Path to runtime output
            agent_configs: Dict mapping character_id → AgentConfig
                          Default: Sonnet for all characters
            use_real_agents: If False, use mock responses (Phase 1 behavior)
            fallback_to_mock: If True, fall back to mock on agent failure
        """
        super().__init__(scenario_path, runtime_path)
        
        self.use_real_agents = use_real_agents
        self.fallback_to_mock = fallback_to_mock
        
        # Set up agent configs (default: Sonnet for all)
        self.agent_configs = agent_configs or self._default_agent_configs()
        
        # Agent call tracking
        self.agent_calls = []  # List of (character, turn, result) tuples

    def _default_agent_configs(self) -> dict[str, AgentConfig]:
        """Create default agent configs (Sonnet for all)."""
        sonnet = LLMConfig("anthropic", "claude-sonnet-4-6")
        return {
            "aeliana": AgentConfig("aeliana", "Aeliana Moonglade", llm=sonnet),
            "fennel": AgentConfig("fennel", "Fennel", llm=sonnet),
            "shadowbeast": AgentConfig("shadowbeast", "Shadowbeast", llm=sonnet),
        }

    def spawn_character_agent(self, character: str, turn: int) -> Optional[str]:
        """
        Spawn a sub-agent to generate character action.
        
        Returns:
            Formatted character response (INTERNAL/BODY_LANGUAGE/SPOKEN/ACTION)
            or None if spawning fails and fallback_to_mock=False
        """
        if not self.use_real_agents:
            # Phase 1 mode: return mock
            return self._get_mock_response(character, turn)
        
        prompt = self.build_character_prompt(character, turn)
        config = self.agent_configs.get(character)
        
        if not config:
            print(f"WARNING: No agent config for {character}, using mock")
            return self._get_mock_response(character, turn) if self.fallback_to_mock else None
        
        print(f"  Spawning {config}...")
        
        try:
            # Build attachments for SOUL.md and IDENTITY.md
            soul = self._load_soul(character)
            identity = self._load_identity(character)
            
            attachments = [
                {
                    "name": f"{character}_SOUL.md",
                    "content": soul,
                    "mimeType": "text/markdown",
                },
                {
                    "name": f"{character}_IDENTITY.md",
                    "content": identity,
                    "mimeType": "text/markdown",
                },
            ]
            
            # Spawn sub-agent
            # NOTE: This is a mock call structure. Real implementation uses OpenClaw's sessions_spawn
            result = self._call_agent(
                task=prompt,
                attachments=attachments,
                config=config,
                timeout_seconds=30,
            )
            
            if result:
                self.agent_calls.append({
                    "character": character,
                    "turn": turn,
                    "config": str(config),
                    "status": "success",
                })
                return result
            else:
                raise Exception("Agent returned empty response")
        
        except Exception as e:
            print(f"  ERROR: Agent spawn failed: {e}")
            
            if self.fallback_to_mock:
                print(f"  Falling back to mock response...")
                self.agent_calls.append({
                    "character": character,
                    "turn": turn,
                    "config": str(config),
                    "status": f"fallback (error: {str(e)})",
                })
                return self._get_mock_response(character, turn)
            else:
                self.agent_calls.append({
                    "character": character,
                    "turn": turn,
                    "config": str(config),
                    "status": f"failed (no fallback)",
                })
                return None

    # Provider → agent class mapping
    AGENT_CLASSES = {
        "anthropic": ClaudeAgent,
        "openai":    ChatGPTAgent,
        "grok":      GrokAgent,
        "ollama":    OllamaAgent,
        "gemini":    GeminiAgent,
        "deepseek":  DeepSeekAgent,
    }

    # Provider → environment variable for API key
    API_KEY_VARS = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai":    "OPENAI_API_KEY",
        "grok":      "XAI_API_KEY",
        "gemini":    "GOOGLE_API_KEY",
        "deepseek":  "DEEPSEEK_API_KEY",
    }

    def _call_agent(self,
                    task: str,
                    attachments: list,
                    config: AgentConfig,
                    timeout_seconds: int = 30) -> Optional[str]:
        """
        Call an LLM agent using engine/agents/ wrappers.

        Uses the provider from config.llm to select the right agent class,
        reads the API key from the corresponding environment variable,
        and runs the async send_message() synchronously.
        """
        provider = config.llm.provider
        model = config.llm.model
        agent_cls = self.AGENT_CLASSES.get(provider)

        if not agent_cls:
            raise ValueError(f"Unknown provider: {provider}")

        # Build system prompt from attachments (SOUL + IDENTITY)
        system_prompt = "\n\n".join(
            f"# {att['name']}\n{att['content']}" for att in attachments
        )

        # Create agent instance
        if provider == "ollama":
            agent = agent_cls(
                name=config.character_id,
                model=model,
                system_prompt=system_prompt,
            )
        else:
            api_key = os.environ.get(self.API_KEY_VARS[provider], "")
            if not api_key:
                raise EnvironmentError(
                    f"{self.API_KEY_VARS[provider]} not set"
                )
            agent = agent_cls(
                name=config.character_id,
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
            )

        print(f"    [{provider}] Calling {model}...")

        # Run the async call synchronously
        async def _run():
            async with aiohttp.ClientSession() as session:
                return await agent.send_message(task, session)

        return asyncio.run(_run())

    def run_turn(self, turn: int) -> None:
        """Execute one full turn — overrides Phase 1 to use agent spawning."""
        print(f"\n{'=' * 70}")
        print(f"TURN {turn}")
        print(f"{'=' * 70}\n")

        self.scene.turn = turn
        self.roll_initiative(seed=42)

        for character in self.initiative_order:
            print(f"\n{character.upper()} ({self.scene.initiative_rolls[character]} initiative)")
            print("-" * 50)

            action = self.process_character_turn(character, turn)
            self.scene.history.append(action)
            print(action.to_scene_entry())

    def process_character_turn(self, character: str, turn: int) -> CharacterAction:
        """
        Process character turn by spawning agent (or using mock).
        
        Overrides Phase 1 to use real agent.
        """
        response = self.spawn_character_agent(character, turn)
        
        if not response:
            print(f"  FATAL: Could not generate response for {character}")
            # Return empty action as fallback
            return CharacterAction(
                character=character,
                turn=turn,
                initiative=self.scene.initiative_rolls.get(character, 0),
                internal="(agent unavailable)",
                body_language="",
                spoken="",
                action="(no action)",
            )
        
        # Parse response (same as Phase 1)
        return self._parse_response(character, turn, response)

    def _parse_response(self, character: str, turn: int, response: str) -> CharacterAction:
        """Parse structured character response into CharacterAction."""
        # Regex-based extraction (same as Phase 1)
        def extract_section(text: str, section: str) -> str:
            pattern = rf"\*\*{section}\*\*\s*(?:—|:)?\s*(.*?)(?=\*\*|\Z)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""

        return CharacterAction(
            character=character,
            turn=turn,
            initiative=self.scene.initiative_rolls.get(character, 0),
            internal=extract_section(response, "INTERNAL"),
            body_language=extract_section(response, "BODY LANGUAGE"),
            spoken=extract_section(response, "SPOKEN"),
            action=extract_section(response, "ACTION"),
        )

    def save_session_log(self) -> None:
        """Save full session transcript with agent call tracking."""
        log_file = self.runtime_path / "session_log.json"
        
        log_data = {
            "session": {
                "final_turn": self.scene.turn,
                "total_actions": len(self.scene.history),
            },
            "agent_calls": self.agent_calls,
            "characters": {
                char_id: {
                    "name": char_obj.character_name,
                    "config": str(self.agent_configs.get(char_id, "unknown")),
                    "final_condition": asdict(char_obj.state),
                }
                for char_id, char_obj in self.characters.items()
            },
        }
        
        log_file.write_text(json.dumps(log_data, indent=2))
        print(f"\nSession log saved to {log_file}")

    def run(self, num_turns: int = 3):
        """Run the full simulation with real agents."""
        print(f"\nFEY GLADE ORCHESTRATOR - PHASE 2 (REAL AGENTS)")
        print(f"Characters: Aeliana (ranger), Fennel (gatherer), Shadowbeast (creature)")
        print(f"LLM Configuration:")
        for char_id, config in self.agent_configs.items():
            print(f"  {config}")
        print(f"Turns: {num_turns}\n")

        for turn_num in range(1, num_turns + 1):
            self.run_turn(turn_num)

        self.save_state()
        self.save_session_log()

        print(f"\n{'=' * 70}")
        print("SIMULATION COMPLETE")
        print(f"{'=' * 70}\n")
        print("Agent call summary:")
        for call in self.agent_calls:
            status = call["status"]
            char = call["character"]
            turn = call["turn"]
            print(f"  Turn {turn}, {char}: {status}")


# =========================================================================
# CLI ENTRY POINT
# =========================================================================

def _parse_model_spec(spec: str) -> LLMConfig:
    """Parse 'provider/model' string into LLMConfig. Default provider is anthropic."""
    if "/" in spec:
        provider, model = spec.split("/", 1)
    else:
        provider, model = "anthropic", spec
    return LLMConfig(provider, model)


def main():
    """Run Phase 2 orchestrator with configurable LLMs."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Driftmoor Fey Glade Orchestrator - Phase 2")
    parser.add_argument("--turns", type=int, default=1, help="Number of turns to simulate")
    parser.add_argument("--mock", action="store_true", help="Use mock responses (Phase 1 mode)")
    parser.add_argument("--no-fallback", action="store_true", help="Don't fallback to mock on agent error")
    parser.add_argument("--aeliana-model", default="anthropic/claude-sonnet-4-6",
                        help="provider/model for Aeliana (e.g. openai/gpt-4o, ollama/qwen3:14b)")
    parser.add_argument("--fennel-model", default="anthropic/claude-sonnet-4-6",
                        help="provider/model for Fennel")
    parser.add_argument("--shadowbeast-model", default="anthropic/claude-sonnet-4-6",
                        help="provider/model for Shadowbeast")
    
    args = parser.parse_args()
    
    # Build custom agent configs
    agent_configs = {
        "aeliana": AgentConfig(
            "aeliana",
            "Aeliana Moonglade",
            llm=_parse_model_spec(args.aeliana_model),
        ),
        "fennel": AgentConfig(
            "fennel",
            "Fennel",
            llm=_parse_model_spec(args.fennel_model),
        ),
        "shadowbeast": AgentConfig(
            "shadowbeast",
            "Shadowbeast",
            llm=_parse_model_spec(args.shadowbeast_model),
        ),
    }
    
    # Create orchestrator
    orchestrator = FeyGladeOrchestratorPhase2(
        agent_configs=agent_configs,
        use_real_agents=not args.mock,
        fallback_to_mock=not args.no_fallback,
    )
    
    # Run simulation
    orchestrator.run(num_turns=args.turns)


if __name__ == "__main__":
    main()
