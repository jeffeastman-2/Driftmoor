"""Conversation orchestrator for managing multi-agent conversations"""

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

from models import Message
from speaker_selection import _detect_direct_address
from metrics import ConversationMetrics


class ConversationOrchestrator:
    """Manages conversations between multiple LLM agents using round-robin with shared transcript"""

    def __init__(self, agents: List, max_turns: int = 10, delay: float = 1.0,
                 agent_descriptions: Dict[str, str] = None, openai_api_key: str = None,
                 agent_providers: Dict[str, str] = None, claude_api_key: str = None):
        self.agents = agents
        self.max_turns = max_turns
        self.delay = delay
        self.conversation_log: List[Message] = []
        self.agent_descriptions = agent_descriptions or {}
        self.openai_api_key = openai_api_key
        self.claude_api_key = claude_api_key
        self.agent_providers = agent_providers or {}
        # Create name-to-agent lookup
        self.agent_by_name = {a.name: a for a in agents}
        
        # Initialize metrics
        agent_names = [a.name for a in agents]
        self.metrics = ConversationMetrics(agent_names, self.agent_providers)
        
        # Initialize monitor agent state
        self.identity_state = {
            a.name: {"history": [], "mood": ""}
            for a in agents
        }
        self.monitor_log: List[dict] = []

    def _build_transcript(self) -> str:
        """Build a formatted transcript from conversation log, showing only visible sections"""
        lines = []
        for msg in self.conversation_log:
            visible = self._extract_visible(msg.content)
            lines.append(f"[{msg.speaker}]: {visible}")
        return "\n\n".join(lines)

    def _extract_visible(self, response: str) -> str:
        """Extract only BODY LANGUAGE + SPOKEN sections (strip INTERNAL).
        
        If the response doesn't follow the section format, return as-is.
        """
        import re
        # Look for section headers
        has_internal = bool(re.search(r'^##\s*INTERNAL', response, re.MULTILINE | re.IGNORECASE))
        has_spoken = bool(re.search(r'^##\s*SPOKEN', response, re.MULTILINE | re.IGNORECASE))
        
        if not (has_internal and has_spoken):
            # Response doesn't follow format — return as-is
            return response
        
        # Split into sections by ## headers
        sections = re.split(r'^##\s*', response, flags=re.MULTILINE)
        
        visible_parts = []
        for section in sections:
            # Skip empty sections and INTERNAL
            if not section.strip():
                continue
            header_match = re.match(r'^(\w[\w\s]*)', section)
            if header_match:
                header = header_match.group(1).strip().upper()
                if header == 'INTERNAL':
                    continue  # Skip — private thoughts
                # Keep BODY LANGUAGE, SPOKEN, and anything else
                content = section[header_match.end():].strip()
                if header == 'BODY LANGUAGE':
                    visible_parts.append(f"*{content}*")
                elif header == 'SPOKEN':
                    visible_parts.append(content)
                else:
                    visible_parts.append(content)
        
        return "\n\n".join(visible_parts) if visible_parts else response

    def _extract_spoken(self, response: str) -> str:
        """Extract only the SPOKEN section for direct-address detection."""
        import re
        match = re.search(r'^##\s*SPOKEN\s*\n(.*?)(?=^##|\Z)', response, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else response

    def _clean_response(self, response: str, agent_names: List[str]) -> str:
        """Strip any speaker prefix the LLM may have added (e.g., '[Mojtaba Khamenei]:')"""
        import re
        # Build pattern to match any agent name prefix
        # Match patterns like "[Name]:" or "[Name]: " at the start
        for name in agent_names:
            # Escape special regex chars in name
            escaped = re.escape(name)
            pattern = rf'^\s*\[{escaped}\]:?\s*'
            response = re.sub(pattern, '', response, count=1, flags=re.IGNORECASE)
        return response.strip()

    def _build_identity_context(self, agent_name: str) -> str:
        """Build a context block from current identity_state for an agent's prompt."""
        lines = ["CURRENT CHARACTER STATES:"]
        for name, state in self.identity_state.items():
            mood_str = f" | Mood: {state['mood']}" if state['mood'] else ""
            lines.append(f"  [{name}]{mood_str}")
            if state['history']:
                for entry in state['history'][-5:]:  # last 5 entries
                    lines.append(f"    - {entry}")
        return "\n".join(lines)

    async def _call_monitor(self, session: aiohttp.ClientSession, speaker: str, spoken_text: str, turn: int):
        """Call Claude Haiku to analyse the last turn and update identity_state."""
        if not self.claude_api_key:
            return

        agent_names = [a.name for a in self.agents]
        names_json = json.dumps(agent_names)

        monitor_prompt = f"""You are a conversation monitor. Analyse this turn and return ONLY valid JSON.

Speaker: {speaker}
What they said:
{spoken_text}

Participants: {names_json}

Return exactly this JSON structure (no markdown, no commentary):
{{
  "convergence_score": <-1 for diverging, 0 for neutral, 1 for converging>,
  "convergence_note": "<one sentence>",
  "characters": {{
    "<name>": {{"history_update": "<what changed for them this turn>", "current_mood": "<their likely mood now>"}}
  }}
}}
Include an entry in characters for every participant: {names_json}"""

        headers = {
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": monitor_prompt}]
        }

        try:
            async with session.post("https://api.anthropic.com/v1/messages",
                                    json=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"   [Monitor API error ({resp.status}): {error_text[:120]}]")
                    return
                data = await resp.json()
                raw = data["content"][0]["text"]

            result = json.loads(raw)

            # Update identity_state
            for name, updates in result.get("characters", {}).items():
                if name in self.identity_state:
                    if updates.get("history_update"):
                        self.identity_state[name]["history"].append(updates["history_update"])
                    if updates.get("current_mood"):
                        self.identity_state[name]["mood"] = updates["current_mood"]

            # Log it
            entry = {
                "turn": turn,
                "speaker": speaker,
                "convergence_score": result.get("convergence_score", 0),
                "convergence_note": result.get("convergence_note", ""),
                "characters": result.get("characters", {}),
                "timestamp": datetime.now().isoformat()
            }
            self.monitor_log.append(entry)

            score = result.get('convergence_score', 0)
            note = result.get('convergence_note', '')
            symbol = {-1: '↘', 0: '→', 1: '↗'}.get(score, '?')
            print(f"   [Monitor {symbol} ({score}): {note[:80]}]")

        except (json.JSONDecodeError, KeyError) as e:
            print(f"   [Monitor parse error: {e}]")
        except Exception as e:
            print(f"   [Monitor error: {e}]")

    def save_monitor_log(self, filename: str):
        """Save the monitor log alongside conversation output."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "identity_state": self.identity_state,
                "log": self.monitor_log
            }, f, indent=2, ensure_ascii=False)
        print(f"✓ Monitor log saved to {filename}")

    def _get_next_in_rotation(self, current_idx: int) -> int:
        """Get next agent index in round-robin order"""
        return (current_idx + 1) % len(self.agents)

    async def run_conversation(self, starting_message: str, starting_agent_idx: int = 0):
        """
        Run a conversation between agents using round-robin with direct-address interrupt.
        
        - Single shared transcript visible to all
        - Round-robin speaking order
        - Direct address (e.g., "President Trump, what do you think?") interrupts order
        """
        async with aiohttp.ClientSession() as session:
            starting_agent = self.agents[starting_agent_idx]
            agent_names = [a.name for a in self.agents]
            
            print(f"\n{'='*70}")
            print(f"Starting conversation with {len(self.agents)} agents")
            print(f"Max turns: {self.max_turns}")
            print(f"Mode: Round-robin with direct-address interrupt")
            print(f"Order: {' → '.join(a.name for a in self.agents)}")
            print(f"{'='*70}\n")

            # Opening message from starting agent (usually mediator)
            print(f"\n--- Opening ---")
            print(f"← {starting_agent.name} says:")
            print(f"  {starting_message[:200]}{'...' if len(starting_message) > 200 else ''}")
            
            # Log the opening message
            self.conversation_log.append(Message(
                speaker=starting_agent.name,
                content=starting_message,
                timestamp=datetime.now()
            ))
            
            # Record opening in metrics
            self.metrics.record_turn(
                speaker=starting_agent.name,
                content=starting_message,
                previous_speaker=None,
                response_time_ms=0
            )
            
            # Determine first responder
            # Check if someone is directly addressed in opening
            other_names = [n for n in agent_names if n != starting_agent.name]
            addressed = _detect_direct_address(starting_message, other_names)
            
            # rotation_idx tracks the pure round-robin position, never modified by interrupts
            if addressed:
                current_idx = agent_names.index(addressed)
                print(f"   [Direct address detected: {addressed}]")
            else:
                current_idx = self._get_next_in_rotation(starting_agent_idx)
            
            # Rotation starts after the opening speaker in the defined order
            # If the first responder was picked by interrupt (not round-robin), 
            # rotation_idx remains at the first natural successor
            rotation_idx = self._get_next_in_rotation(starting_agent_idx)
            # Advance past the interrupt pick if it matches
            if rotation_idx == current_idx:
                rotation_idx = self._get_next_in_rotation(rotation_idx)
            
            previous_speaker = starting_agent.name
            consecutive_interrupts = 1 if addressed else 0
            MAX_CONSECUTIVE_INTERRUPTS = 2  # Force rotation after this many direct-address interrupts

            for turn in range(self.max_turns):
                current_agent = self.agents[current_idx]
                
                print(f"\n--- Turn {turn + 1} ---")
                
                # Build transcript for this agent
                transcript = self._build_transcript()
                
                # Create the prompt: transcript + identity context + instruction
                identity_context = self._build_identity_context(current_agent.name)
                prompt = f"""CONVERSATION SO FAR:
{transcript}

---
{identity_context}

---
You are {current_agent.name}. It is now your turn to speak. Respond ONLY as {current_agent.name} — do not write dialogue or thoughts for any other participant."""

                print(f"→ {current_agent.name}'s turn")

                try:
                    # Clear agent's history for stateless operation
                    current_agent.conversation_history = []
                    
                    # Time the API call
                    start_time = time.time()
                    response = await current_agent.send_message(prompt, session)
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    # Clean any speaker prefix the LLM may have added
                    response = self._clean_response(response, agent_names)

                    # Log the response
                    msg = Message(
                        speaker=current_agent.name,
                        content=response,
                        timestamp=datetime.now()
                    )
                    self.conversation_log.append(msg)
                    
                    # Record metrics
                    self.metrics.record_turn(
                        speaker=current_agent.name,
                        content=response,
                        previous_speaker=previous_speaker,
                        response_time_ms=response_time_ms
                    )

                    print(f"← {current_agent.name} responds:")
                    print(f"  {response[:200]}{'...' if len(response) > 200 else ''}")

                    # Run monitor agent
                    await self._call_monitor(session, current_agent.name, response, turn + 1)

                    previous_speaker = current_agent.name

                    # Determine next speaker
                    # Check for direct address in the SPOKEN section only
                    other_names = [n for n in agent_names if n != current_agent.name]
                    spoken = self._extract_spoken(response)
                    addressed = _detect_direct_address(spoken, other_names)
                    
                    if addressed and consecutive_interrupts < MAX_CONSECUTIVE_INTERRUPTS:
                        # Interrupt: addressed person speaks next
                        next_idx = agent_names.index(addressed)
                        consecutive_interrupts += 1
                        print(f"   [Direct address → {addressed}] (interrupt {consecutive_interrupts}/{MAX_CONSECUTIVE_INTERRUPTS})")
                        # rotation_idx stays unchanged — interrupts don't affect round-robin position
                    else:
                        # Force rotation - either no direct address, or max interrupts reached
                        if addressed:
                            print(f"   [Max interrupts reached, forcing rotation]")
                        consecutive_interrupts = 0  # Reset counter
                        
                        # Normal round-robin: advance to next in rotation
                        # Skip the current speaker if rotation lands on them
                        next_idx = rotation_idx
                        if next_idx == current_idx:
                            next_idx = self._get_next_in_rotation(next_idx)
                        rotation_idx = self._get_next_in_rotation(next_idx)
                        print(f"   [Round-robin → {self.agents[next_idx].name}]")
                    
                    current_idx = next_idx

                    # Delay between turns
                    await asyncio.sleep(self.delay)

                except Exception as e:
                    print(f"\n❌ Error with {current_agent.name}: {e}")
                    import traceback
                    traceback.print_exc()
                    break

    def save_conversation(self, filename: str = "conversation_log.json"):
        """Save the conversation to a JSON file"""
        log_data = [
            {
                "speaker": msg.speaker,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.conversation_log
        ]

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Conversation saved to {filename}")

    def _sanitize_for_pdf(self, text):
        """Replace Unicode characters that aren't supported by standard PDF fonts"""
        replacements = {
            '\u2014': '--',   # em-dash
            '\u2013': '-',    # en-dash
            '\u2018': "'",    # left single quote
            '\u2019': "'",    # right single quote
            '\u201c': '"',    # left double quote
            '\u201d': '"',    # right double quote
            '\u2026': '...',  # ellipsis
            '\u2022': '*',    # bullet
            '\u00a0': ' ',    # non-breaking space
            '\u200b': '',     # zero-width space
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text.encode('latin-1', errors='replace').decode('latin-1')

    def save_conversation_pdf(self, filename: str, title: str = "Conversation"):
        """Save the conversation to a PDF file"""
        if not HAS_FPDF:
            print("\n⚠️  PDF export requires fpdf2: pip install fpdf2")
            return False
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 15, self._sanitize_for_pdf(title), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)
        
        # Speaker colors (RGB)
        colors = [
            (41, 128, 185),   # Blue
            (39, 174, 96),    # Green  
            (192, 57, 43),    # Red
            (142, 68, 173),   # Purple
            (243, 156, 18),   # Orange
        ]
        speaker_colors = {}
        
        for i, msg in enumerate(self.conversation_log, 1):
            # Assign color to speaker
            if msg.speaker not in speaker_colors:
                speaker_colors[msg.speaker] = colors[len(speaker_colors) % len(colors)]
            
            color = speaker_colors[msg.speaker]
            
            # Speaker header with timestamp
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*color)
            header = f"[{msg.timestamp.strftime('%H:%M:%S')}] {msg.speaker}"
            pdf.cell(0, 8, self._sanitize_for_pdf(header), new_x="LMARGIN", new_y="NEXT")
            
            # Message content
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            
            # Handle multi-line content - fpdf2 multi_cell for text wrapping
            content = self._sanitize_for_pdf(msg.content.replace('\r', ''))
            pdf.multi_cell(0, 5, content)
            pdf.ln(5)
            
            # Separator line
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
        
        pdf.output(filename)
        print(f"✓ PDF saved to {filename}")
        return True

    def print_full_conversation(self):
        """Print the complete conversation"""
        print("\n" + "="*70)
        print("FULL CONVERSATION")
        print("="*70)
        for i, msg in enumerate(self.conversation_log, 1):
            print(f"\n[{msg.timestamp.strftime('%H:%M:%S')}] {msg.speaker} (message {i}):")
            print(f"{msg.content}")
            print("-" * 70)
