import json
from typing import Any, Dict

import openai

from presentiq.ai.agents.schemas import AGENT_SCHEMAS
from presentiq.ai.backend import AnalysisError


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
        if self.model.startswith("gpt-5"):
            response = self.client.responses.parse(
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
                reasoning={"effort": "low"},
                max_output_tokens=max_tokens + 4000,
                text_format=AGENT_SCHEMAS[self.agent_name],
                store=False,
            )
            if response.status != "completed" or response.output_parsed is None:
                raise AnalysisError("The model did not finish its evaluation. Please retry.")
            return response.output_parsed.model_dump_json()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        if choice.finish_reason != "stop" or not choice.message.content:
            raise AnalysisError("The model did not finish its evaluation. Please retry.")
        return choice.message.content.strip()

    def _call_llm_json(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 1500
    ) -> Dict[str, Any]:
        try:
            raw = self._call_llm(system_prompt, user_prompt, max_tokens)
            if raw.startswith("```json"):
                raw = raw[len("```json") :].strip()
            elif raw.startswith("```"):
                raw = raw[3:].strip()
            if raw.endswith("```"):
                raw = raw[:-3].strip()
            return AGENT_SCHEMAS[self.agent_name].model_validate(json.loads(raw)).model_dump()
        except Exception as exc:
            # Provider errors may contain credentials or presentation text. Never
            # embed the raw exception in feedback, exports, or client responses.
            raise AnalysisError(
                f"The {self.agent_name.replace('_', ' ')} evaluation could not be completed. "
                "No score was saved. Please retry."
            ) from exc

    @staticmethod
    def format_guidance(context):
        config = context.get("format_config", {})
        return (
            f"PRESENTATION FORMAT: {config.get('name', 'Full H&P')}\n"
            f"EXPECTED SECTIONS: {', '.join(config.get('expected_sections', []))}\n"
            f"FORMAT PRIORITIES: {', '.join(config.get('evaluation_focus', []))}\n"
            "Judge completeness, reasoning depth, and audience adaptation against this format. "
            "Do not require a full H&P for an SBAR, handoff, consult, or brief update."
        )
