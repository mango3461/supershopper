import json
from urllib import error, request

from app.api.schemas.common import (
    BudgetPayload,
    EvidenceFilteringPayload,
    IntentAnalysisPayload,
    ProductPayload,
    RecommendationWordingPayload,
    SearchStrategyPayload,
    SummaryPayload,
    UserQueryPayload,
)
from app.ports.llm_port import LLMPort
from app.services.llm_fallbacks import LLMFallbackService


class MockLLMAdapter(LLMPort):
    provider_name = "mock-llm"
    mode = "mock"

    def __init__(self) -> None:
        self._fallbacks = LLMFallbackService()

    def generate_intent_analysis(
        self, user_query: UserQueryPayload, prompt: str
    ) -> IntentAnalysisPayload | None:
        del prompt
        return self._fallbacks.build_intent_analysis(user_query)

    def generate_search_strategy(
        self, intent: IntentAnalysisPayload, prompt: str, max_candidates: int
    ) -> SearchStrategyPayload | None:
        del prompt
        return self._fallbacks.build_search_strategy(intent, max_candidates)

    def generate_buying_guide_summary(
        self, intent: IntentAnalysisPayload, filtered: EvidenceFilteringPayload, prompt: str
    ) -> SummaryPayload | None:
        del prompt
        return self._fallbacks.build_buying_guide_summary(intent, filtered)

    def generate_recommendation_wording(
        self,
        intent: IntentAnalysisPayload,
        shortlisted_candidates: list[ProductPayload],
        recommended_choice: ProductPayload | None,
        summary: SummaryPayload,
        prompt: str,
    ) -> RecommendationWordingPayload | None:
        del prompt
        return self._fallbacks.build_recommendation_wording(
            intent=intent,
            shortlisted_candidates=shortlisted_candidates,
            recommended_choice=recommended_choice,
            summary=summary,
        )


class OpenAIAdapter(MockLLMAdapter):
    provider_name = "openai"
    mode = "configured"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 20.0,
    ) -> None:
        super().__init__()
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def generate_intent_analysis(
        self, user_query: UserQueryPayload, prompt: str
    ) -> IntentAnalysisPayload | None:
        schema_instruction = """
Return only valid JSON with this exact shape:
{
  "category": "mechanical_keyboard",
  "category_label": "Mechanical Keyboard",
  "user_level": "beginner|intermediate|advanced",
  "use_case": "string",
  "budget": {
    "currency": "KRW",
    "min_price": null,
    "max_price": null
  },
  "constraints": ["string"],
  "prioritized_attributes": ["noise", "key feel", "layout", "price"],
  "preferred_noise_level": "quiet|undecided",
  "preferred_key_feel": "silent_linear|silent_tactile|silent_linear_or_tactile|linear|tactile|clicky|undecided",
  "preferred_layout": "75%|TKL|full_size|undecided",
  "desired_features": ["string"],
  "comparison_axes": ["string"],
  "interpretation_summary": "string",
  "confidence_score": 0.0
}
Rules:
- Keep category fixed as "mechanical_keyboard".
- Budget values must be integers or null.
- Confidence score must be between 0 and 1.
- If unclear, still fill the fields conservatively instead of omitting them.
""".strip()
        full_prompt = f"{prompt}\n\n{schema_instruction}\n"
        raw_text = self._call_openai_json_prompt(full_prompt, user_query.query)
        if not raw_text:
            return None

        parsed = json.loads(raw_text)
        return IntentAnalysisPayload(
            original_query=user_query.query,
            category=parsed.get("category", "mechanical_keyboard"),
            category_label=parsed.get("category_label", "Mechanical Keyboard"),
            user_level=parsed.get("user_level", "beginner"),
            use_case=parsed.get("use_case", "First mechanical keyboard purchase"),
            budget=BudgetPayload(
                currency=(parsed.get("budget") or {}).get("currency", "KRW"),
                min_price=(parsed.get("budget") or {}).get("min_price"),
                max_price=(parsed.get("budget") or {}).get("max_price"),
            ),
            constraints=parsed.get("constraints") or [],
            prioritized_attributes=parsed.get("prioritized_attributes") or [],
            preferred_noise_level=parsed.get("preferred_noise_level", "undecided"),
            preferred_key_feel=parsed.get("preferred_key_feel", "undecided"),
            preferred_layout=parsed.get("preferred_layout", "undecided"),
            desired_features=parsed.get("desired_features") or [],
            comparison_axes=parsed.get("comparison_axes") or [],
            interpretation_summary=parsed.get("interpretation_summary", ""),
            confidence_score=parsed.get("confidence_score", 0.0),
        )

    def _call_openai_json_prompt(self, prompt: str, user_query: str) -> str | None:
        payload = {
            "model": self._model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "You are an assistant that extracts structured shopping intent as strict JSON.",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"{prompt}\n\nUser query:\n{user_query}",
                        }
                    ],
                },
            ],
        }
        request_body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            url=f"{self._base_url}/responses",
            data=request_body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI network error: {exc.reason}") from exc

        text = self._extract_response_text(response_payload)
        if not text:
            raise RuntimeError("OpenAI response did not contain text output")
        return text

    @staticmethod
    def _extract_response_text(response_payload: dict) -> str | None:
        output_text = response_payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        output_items = response_payload.get("output")
        if not isinstance(output_items, list):
            return None

        collected_text: list[str] = []
        for item in output_items:
            if not isinstance(item, dict):
                continue
            content_items = item.get("content")
            if not isinstance(content_items, list):
                continue
            for content in content_items:
                if not isinstance(content, dict):
                    continue
                text_value = content.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    collected_text.append(text_value.strip())

        if not collected_text:
            return None
        return "\n".join(collected_text)
