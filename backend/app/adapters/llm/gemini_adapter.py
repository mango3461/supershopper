import json
import logging
from urllib import error, request

from app.adapters.llm.openai_adapter import MockLLMAdapter
from app.api.schemas.common import IntentAnalysisPayload, SearchQuery, SearchStrategyPayload


class GeminiAdapter(MockLLMAdapter):
    provider_name = "gemini"
    mode = "configured"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1",
        timeout_seconds: float = 20.0,
    ) -> None:
        super().__init__()
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._logger = logging.getLogger("supershopper.gemini")

    def generate_search_strategy(
        self, intent: IntentAnalysisPayload, prompt: str, max_candidates: int
    ) -> SearchStrategyPayload | None:
        self._logger.info(
            "Gemini generate_search_strategy start model=%s budget_max=%s max_candidates=%s",
            self._model,
            intent.budget.max_price,
            max_candidates,
        )
        schema_instruction = """
Return only valid JSON with this exact shape:
{
  "queries": [
    {
      "query": "string",
      "rationale": "string"
    }
  ],
  "strategy_note": "string",
  "max_products": 0
}
Rules:
- Generate 3 concise shopping search queries when possible. Never return fewer than 2.
- Every query must be about mechanical keyboards and should help compare beginner-friendly options.
- Keep the queries concrete and searchable.
- max_products must be an integer between 4 and 6.
""".strip()
        full_prompt = f"{prompt}\n\n{schema_instruction}\n"
        raw_text = self._call_gemini_json_prompt(full_prompt, intent, max_candidates)
        if not raw_text:
            self._logger.warning("Gemini returned empty text for generate_search_strategy")
            return None

        parsed = json.loads(raw_text)
        payload = SearchStrategyPayload(
            queries=[
                SearchQuery(
                    query=item.get("query", "").strip(),
                    rationale=item.get("rationale", "").strip(),
                )
                for item in parsed.get("queries", [])
                if isinstance(item, dict)
            ],
            sources=["mock_shopping_catalog", "mock_editorial_reviews", "mock_user_reviews"],
            max_products=parsed.get("max_products", max(max_candidates + 2, 4)),
            strategy_note=str(parsed.get("strategy_note", "")).strip(),
        )
        if not self._is_high_quality_search_strategy(payload):
            self._logger.warning(
                "Gemini search strategy rejected by quality validation query_count=%s",
                len(payload.queries),
            )
            return None
        self._logger.info(
            "Gemini generate_search_strategy success query_count=%s max_products=%s",
            len(payload.queries),
            payload.max_products,
        )
        return payload

    def _call_gemini_json_prompt(
        self, prompt: str, intent: IntentAnalysisPayload, max_candidates: int
    ) -> str | None:
        final_url = self._build_generate_content_url()
        request_payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You generate high-quality shopping search strategies for a mechanical "
                            "keyboard recommendation workflow. Return strict JSON only."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                f"{prompt}\n\n"
                                f"Intent category: {intent.category}\n"
                                f"User level: {intent.user_level}\n"
                                f"Budget max: {intent.budget.max_price}\n"
                                f"Preferred noise: {intent.preferred_noise_level}\n"
                                f"Preferred key feel: {intent.preferred_key_feel}\n"
                                f"Preferred layout: {intent.preferred_layout}\n"
                                f"Constraints: {intent.constraints}\n"
                                f"Desired features: {intent.desired_features}\n"
                                f"Target shortlist size: {max_candidates}\n"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": {
                    "type": "object",
                    "required": ["queries", "strategy_note", "max_products"],
                    "properties": {
                        "queries": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 4,
                            "items": {
                                "type": "object",
                                "required": ["query", "rationale"],
                                "properties": {
                                    "query": {"type": "string"},
                                    "rationale": {"type": "string"},
                                },
                            },
                        },
                        "strategy_note": {"type": "string"},
                        "max_products": {"type": "integer"},
                    },
                },
                "thinkingConfig": {
                    "thinkingBudget": 0
                },
            },
        }
        http_request = request.Request(
            url=final_url,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "x-goog-api-key": self._api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            self._logger.info(
                "Calling Gemini API model=%s final_url=%s",
                self._model,
                final_url,
            )
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            self._logger.error("Gemini HTTP error status=%s detail=%s", exc.code, detail)
            raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            self._logger.error("Gemini network error detail=%s", exc.reason)
            raise RuntimeError(f"Gemini network error: {exc.reason}") from exc

        text = self._extract_response_text(response_payload)
        if not text:
            self._logger.error("Gemini response did not contain text output")
            raise RuntimeError("Gemini response did not contain text output")
        self._logger.info("Gemini API response received successfully final_url=%s", final_url)
        return text

    def _build_generate_content_url(self) -> str:
        base = self._base_url.strip()
        if not base.startswith(("http://", "https://")):
            base = f"https://{base.lstrip('/')}"
        base = base.rstrip("/")

        if ":generateContent" in base:
            return base

        return f"{base}/models/{self._model}:generateContent"

    @staticmethod
    def _extract_response_text(response_payload: dict) -> str | None:
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list):
            return None

        collected_text: list[str] = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            if not isinstance(content, dict):
                continue
            parts = content.get("parts")
            if not isinstance(parts, list):
                continue
            for part in parts:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    collected_text.append(text.strip())

        if not collected_text:
            return None
        return "\n".join(collected_text)

    @staticmethod
    def _is_high_quality_search_strategy(payload: SearchStrategyPayload) -> bool:
        if len(payload.queries) < 2:
            return False
        if not payload.strategy_note:
            return False
        if payload.max_products < 4 or payload.max_products > 6:
            return False

        seen_queries: set[str] = set()
        allowed_keywords = [
            "키보드",
            "기계식",
            "keyboard",
            "switch",
            "스위치",
            "배열",
            "텐키리스",
            "저소음",
            "적축",
            "갈축",
        ]
        strong_query_count = 0

        for item in payload.queries:
            normalized_query = item.query.strip().lower()
            normalized_rationale = item.rationale.strip()
            if len(normalized_query) < 8 or len(normalized_rationale) < 8:
                return False
            if normalized_query in seen_queries:
                return False
            seen_queries.add(normalized_query)
            if any(keyword in item.query.lower() for keyword in allowed_keywords):
                strong_query_count += 1

        return strong_query_count >= 2
