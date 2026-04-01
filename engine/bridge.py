"""
Multi-LLM API Bridge
Connect Claude, ChatGPT, and Grok to talk with each other
"""

import asyncio
import os
import sys
import json
from pathlib import Path

from agents import ClaudeAgent, ChatGPTAgent, GrokAgent, OllamaAgent, GeminiAgent, DeepSeekAgent
from orchestrator import ConversationOrchestrator


def load_text_file(base_dir: Path, filepath: str) -> str:
    """Load text content from a file relative to base_dir"""
    full_path = base_dir / filepath
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ File not found: {full_path}")
        return ""


def load_persona(base_dir: Path, persona_dir: str, scenario_name: str = None) -> str:
    """Load persona from a people/ directory structure.
    
    Combines SOUL.md (core character) + IDENTITY.md (scenario-specific) into
    a single system prompt. Also loads any additional .md files in the directory.
    """
    persona_path = base_dir / persona_dir
    
    if not persona_path.exists():
        print(f"❌ Persona directory not found: {persona_path}")
        return ""
    
    parts = []
    
    # Load SOUL.md first (core character traits)
    soul_file = persona_path / "SOUL.md"
    if soul_file.exists():
        with open(soul_file, 'r', encoding='utf-8') as f:
            parts.append(f.read().strip())
    
    # Load IDENTITY.md second (scenario-specific position)
    identity_file = persona_path / "IDENTITY.md"
    if identity_file.exists():
        content = identity_file.read_text(encoding='utf-8').strip()
        # Replace placeholder with actual scenario name if provided
        if scenario_name:
            content = content.replace("[SCENARIO NAME]", scenario_name)
        parts.append(content)
    
    # Load any additional .md files (alphabetically, excluding SOUL and IDENTITY)
    for md_file in sorted(persona_path.glob("*.md")):
        if md_file.name not in ("SOUL.md", "IDENTITY.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                parts.append(f.read().strip())
    
    if not parts:
        print(f"⚠️  No .md files found in {persona_path}")
        return ""
    
    return "\n\n---\n\n".join(parts)


def resolve_provider(provider: str, run_llm: str) -> str:
    """Resolve 'run_default' to the actual provider for this run"""
    if provider == "run_default":
        # Map the run's LLM to a provider
        if run_llm.startswith("qwen") or run_llm.startswith("llama") or run_llm.startswith("mistral"):
            return "ollama"
        return run_llm
    return provider


def create_agent(name: str, provider: str, api_keys: dict, system_prompt: str, model: str = None):
    """Create an agent instance based on provider"""
    if provider == "claude":
        return ClaudeAgent(name=name, api_key=api_keys[provider], system_prompt=system_prompt)
    elif provider == "chatgpt":
        return ChatGPTAgent(name=name, api_key=api_keys[provider], system_prompt=system_prompt)
    elif provider == "grok":
        return GrokAgent(name=name, api_key=api_keys[provider], system_prompt=system_prompt)
    elif provider == "gemini":
        return GeminiAgent(name=name, api_key=api_keys[provider], system_prompt=system_prompt)
    elif provider == "deepseek":
        return DeepSeekAgent(name=name, api_key=api_keys[provider], system_prompt=system_prompt)
    elif provider == "ollama":
        model = model or "qwen3:14b"
        return OllamaAgent(name=name, model=model, system_prompt=system_prompt)
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def run_single_scenario(scenario: dict, scenario_dir: Path, api_keys: dict, 
                              run_config: dict = None, output_suffix: str = ""):
    """Run a single scenario configuration"""
    
    run_llm = run_config.get("llm", "claude") if run_config else "claude"
    run_label = run_config.get("label", "") if run_config else ""
    
    # Load dialog rules if present (applies to all agents)
    dialog_rules = ""
    dialog_rules_file = scenario_dir / "dialog_rules.md"
    if dialog_rules_file.exists():
        dialog_rules = dialog_rules_file.read_text(encoding='utf-8').strip()
        print(f"📋 Loaded dialog rules from {dialog_rules_file.name}")
    
    # Create agents from scenario
    agents = []
    agent_providers = {}
    agent_descriptions = {}
    
    for agent_config in scenario.get("agents", []):
        name = agent_config.get("name", "Agent")
        raw_provider = agent_config.get("provider", "claude").lower()
        provider = resolve_provider(raw_provider, run_llm)
        
        # Get model for ollama
        model = None
        if provider == "ollama":
            if raw_provider == "run_default":
                model = run_llm  # Use the run's LLM model
            else:
                model = agent_config.get("model", "qwen3:14b")
        
        # Load system prompt from persona_dir, file, or inline
        scenario_title = scenario.get("title", "")
        if "persona_dir" in agent_config:
            system_prompt = load_persona(scenario_dir, agent_config["persona_dir"], scenario_title)
        elif "system_prompt_file" in agent_config:
            system_prompt = load_text_file(scenario_dir, agent_config["system_prompt_file"])
        else:
            system_prompt = agent_config.get("system_prompt", "")
        
        # Append dialog rules if loaded
        if dialog_rules and system_prompt:
            system_prompt = f"{system_prompt}\n\n---\n\n{dialog_rules}"
        
        if not api_keys.get(provider):
            print(f"❌ Missing API key for {provider.upper()}")
            print(f"Set it with: export {provider.upper()}_API_KEY='your-key-here'")
            return
        
        agent = create_agent(name, provider, api_keys, system_prompt, model)
        agents.append(agent)
        agent_providers[name] = provider
        
        # Build description for speaker selection
        if system_prompt:
            agent_descriptions[name] = system_prompt[:500]
        else:
            agent_descriptions[name] = f"A participant named {name}"
    
    if len(agents) < 2:
        print("❌ Scenario must have at least 2 agents")
        return
    
    # Get scenario settings
    title = scenario.get("title", "Conversation")
    if run_label:
        title = f"{title} - {run_label}"
    max_turns = scenario.get("max_turns", 6)
    
    # Load starting message from file or inline
    if "scenario_file" in scenario:
        starting_message = load_text_file(scenario_dir, scenario["scenario_file"])
    else:
        starting_message = scenario.get("starting_message", "Hello! Let's have a conversation.")
    
    # Generate output filename
    scenario_name = scenario_dir.name if scenario_dir.name != "." else Path(scenario_dir).stem
    if output_suffix:
        scenario_name = f"{scenario_name}_{output_suffix}"
    
    conversations_dir = Path("conversations")
    conversations_dir.mkdir(exist_ok=True)
    output_file = conversations_dir / f"{scenario_name}_conversation.json"
    
    print(f"\n📝 {title}")
    orchestrator = ConversationOrchestrator(
        agents=agents,
        max_turns=max_turns,
        delay=0.5,
        agent_descriptions=agent_descriptions,
        openai_api_key=api_keys.get("chatgpt"),
        agent_providers=agent_providers,
        claude_api_key=api_keys.get("claude")
    )
    
    await orchestrator.run_conversation(
        starting_message=starting_message,
        starting_agent_idx=0
    )
    
    orchestrator.print_full_conversation()
    orchestrator.save_conversation(output_file)
    
    # Save PDF version
    pdf_file = conversations_dir / f"{scenario_name}_conversation.pdf"
    orchestrator.save_conversation_pdf(pdf_file, title=title)
    
    # Save monitor log
    monitor_file = conversations_dir / f"{scenario_name}_monitor.json"
    orchestrator.save_monitor_log(monitor_file)
    
    # Print and save metrics
    orchestrator.metrics.print_summary()
    metrics_file = conversations_dir / f"{scenario_name}_metrics.json"
    orchestrator.metrics.save_report(metrics_file)


async def main():
    """Run a conversation from a scenario JSON file or directory"""

    import argparse
    parser = argparse.ArgumentParser(description="Multi-LLM conversation bridge")
    parser.add_argument("scenario", nargs="?", help="Scenario JSON file or directory")
    parser.add_argument("--config", "-c", default="config.json",
                        help="Config filename to use inside a scenario directory (default: config.json)")
    args = parser.parse_args()

    if not args.scenario:
        print("Usage: python bridge.py <scenario_dir/> [--config CONFIG_FILE]")
        print("\nExamples:")
        print("  python bridge.py scenarios/wargame/")
        print("  python bridge.py scenarios/wargame/ --config config_men.json")
        print("  python bridge.py scenarios/wargame/ -c config_female.json")
        print("\nAvailable scenarios:")
        scenarios_dir = Path("scenarios")
        if scenarios_dir.exists():
            for f in scenarios_dir.glob("*.json"):
                print(f"  • {f}")
            for d in scenarios_dir.iterdir():
                if d.is_dir():
                    configs = sorted(d.glob("config*.json"))
                    if configs:
                        names = ", ".join(c.name for c in configs)
                        print(f"  • {d}/  [{names}]")
        return

    scenario_path = Path(args.scenario)
    
    # API Keys - load from environment variables
    CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    GROK_API_KEY = os.environ.get("GROK_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    DEEPSEEK_API_KEY = os.environ.get("DEEP_SEEK_API_KEY")

    # Map providers to API keys
    api_keys = {
        "claude": CLAUDE_API_KEY,
        "chatgpt": OPENAI_API_KEY,
        "grok": GROK_API_KEY,
        "gemini": GEMINI_API_KEY,
        "deepseek": DEEPSEEK_API_KEY,
        "ollama": "local"
    }
    
    # Determine if this is a directory-based scenario or a single JSON file
    if scenario_path.is_dir():
        config_file = scenario_path / args.config
        if not config_file.exists():
            print(f"❌ Config file not found: {config_file}")
            available = sorted(scenario_path.glob("config*.json"))
            if available:
                print(f"   Available configs: {', '.join(c.name for c in available)}")
            return
        scenario_dir = scenario_path
        scenario_file = config_file
        print(f"📂 Using config: {config_file.name}")
    else:
        scenario_dir = scenario_path.parent
        scenario_file = scenario_path
    
    # Load scenario
    try:
        with open(scenario_file, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
    except FileNotFoundError:
        print(f"❌ Scenario file not found: {scenario_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {scenario_file}: {e}")
        return
    
    # Clear old conversation outputs
    conversations_dir = Path("conversations")
    if conversations_dir.exists():
        for old_file in conversations_dir.glob("*.json"):
            old_file.unlink()
        for old_file in conversations_dir.glob("*.pdf"):
            old_file.unlink()
        print("🗑️  Cleared old conversation files")

    # Check if this is a multi-run scenario
    runs = scenario.get("runs", [])
    
    if runs:
        print(f"\n🎮 Multi-run scenario: {scenario.get('title', 'Wargame')}")
        print(f"   {len(runs)} runs configured")
        print("="*70)
        
        for i, run_config in enumerate(runs, 1):
            print(f"\n{'='*70}")
            print(f"🎯 RUN {i}/{len(runs)}: {run_config.get('label', run_config.get('llm'))}")
            print(f"{'='*70}")
            
            # Create a suffix for this run's output files
            suffix = run_config.get("llm", f"run{i}").replace(":", "_")
            
            await run_single_scenario(
                scenario=scenario,
                scenario_dir=scenario_dir,
                api_keys=api_keys,
                run_config=run_config,
                output_suffix=suffix
            )
            
            # Brief pause between runs
            if i < len(runs):
                print(f"\n⏳ Starting next run in 3 seconds...")
                await asyncio.sleep(3)
        
        print(f"\n{'='*70}")
        print(f"✅ Completed all {len(runs)} runs")
        print(f"{'='*70}")
    else:
        # Single run (legacy format)
        await run_single_scenario(
            scenario=scenario,
            scenario_dir=scenario_dir,
            api_keys=api_keys
        )


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
