import openai
import os
import json
from typing import Dict, Any, Optional


class BaseAgent:
    agent_name: str = "base"
    agent_description: str = "Base agent"

    def __init__(self, client: openai.OpenAI, model: str, temperature: float = 0.3):
        self.client = client
        self.model = model
        self.temperature = temperature

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def _call_llm_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> Dict[str, Any]:
        raw = self._call_llm(system_prompt, user_prompt, max_tokens)

        if raw.startswith("```json"):
            raw = raw[len("```json"):].strip()
        if raw.startswith("```"):
            raw = raw[len("```"):].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

        return json.loads(raw)
