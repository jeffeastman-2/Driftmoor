"""DeepSeek API agent using OpenAI-compatible API"""

import aiohttp


class DeepSeekAgent:
    """DeepSeek API agent using OpenAI-compatible API"""

    def __init__(self, name: str, api_key: str, model: str = "deepseek-chat", system_prompt: str = None):
        self.name = name
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.base_url = "https://api.deepseek.com/chat/completions"

    async def send_message(self, message: str, session: aiohttp.ClientSession) -> str:
        """Send message to DeepSeek and get response"""

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Build messages with system prompt prepended
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(self.conversation_history)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 2048
        }

        async with session.post(self.base_url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                response = data["choices"][0]["message"]["content"]

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

                return response
            else:
                error_text = await resp.text()
                raise Exception(f"DeepSeek API error ({resp.status}): {error_text}")
