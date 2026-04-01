"""Ollama agent for running local LLMs"""

import aiohttp


class OllamaAgent:
    """Agent for local Ollama models (Qwen, Llama, Mistral, etc.)"""

    def __init__(self, name: str, model: str = "qwen3:14b", system_prompt: str = None,
                 base_url: str = "http://localhost:11434"):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.base_url = base_url.rstrip("/")
        self.api_key = None  # Not needed for local Ollama

    async def send_message(self, message: str, session: aiohttp.ClientSession) -> str:
        """Send message to Ollama and get response"""

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Build messages list with system prompt
        messages = []
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        messages.extend(self.conversation_history)

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": 4096  # Context window
            },
            "think": False  # Disable Qwen3 thinking mode for faster responses
        }

        url = f"{self.base_url}/api/chat"
        
        # Longer timeout for local models (can be slow, especially with thinking)
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
        
        try:
            async with session.post(url, json=payload, timeout=timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response = data["message"]["content"]

                    # Add assistant response to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response
                    })

                    return response
                else:
                    error_text = await resp.text()
                    raise Exception(f"Ollama API error ({resp.status}): {error_text}")
        except aiohttp.ClientConnectorError:
            raise Exception(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
