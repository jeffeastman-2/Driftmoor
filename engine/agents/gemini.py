"""Gemini API agent using Google's Generative AI API"""

import aiohttp


class GeminiAgent:
    """Gemini API agent using Google's Generative AI API"""

    def __init__(self, name: str, api_key: str, model: str = "gemini-2.5-flash", system_prompt: str = None):
        self.name = name
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def send_message(self, message: str, session: aiohttp.ClientSession) -> str:
        """Send message to Gemini and get response"""

        # Build contents array with conversation history
        contents = []
        
        # Add conversation history
        for msg in self.conversation_history:
            contents.append({
                "role": msg["role"],
                "parts": [{"text": msg["content"]}]
            })
        
        # Add current user message
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": 2048,
                "temperature": 0.7,
                "thinkingConfig": {"thinkingBudget": 0}  # Disable thinking for faster responses
            }
        }
        
        # Add system instruction if provided
        if self.system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": self.system_prompt}]
            }

        url = f"{self.base_url}?key={self.api_key}"

        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                response = data["candidates"][0]["content"]["parts"][0]["text"]

                # Add to history
                self.conversation_history.append({
                    "role": "user",
                    "content": message
                })
                self.conversation_history.append({
                    "role": "model",
                    "content": response
                })

                return response
            else:
                error_text = await resp.text()
                raise Exception(f"Gemini API error ({resp.status}): {error_text}")
