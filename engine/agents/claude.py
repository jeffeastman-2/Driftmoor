"""Claude API agent using Anthropic's API"""

import aiohttp


class ClaudeAgent:
    """Claude API agent using Anthropic's API"""

    def __init__(self, name: str, api_key: str, model: str = "claude-sonnet-4-5-20250929", system_prompt: str = None):
        self.name = name
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.base_url = "https://api.anthropic.com/v1/messages"

    async def send_message(self, message: str, session: aiohttp.ClientSession) -> str:
        """Send message to Claude and get response"""

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": self.conversation_history
        }
        
        if self.system_prompt:
            payload["system"] = self.system_prompt

        async with session.post(self.base_url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                response = data["content"][0]["text"]

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

                return response
            else:
                error_text = await resp.text()
                raise Exception(f"Claude API error ({resp.status}): {error_text}")
