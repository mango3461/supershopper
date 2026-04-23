import hashlib
import json
import logging
import re
from urllib import error, parse, request

from app.adapters.search.review_search_adapter import ReviewSearchAdapter
from app.adapters.search.shopping_search_adapter import ShoppingSearchAdapter
from app.api.schemas.common import (
    CandidateSeedPayload,
    ExpertSignalPayload,
    ProductPayload,
    ReviewSnippet,
    SearchQuery,
    SearchStrategyPayload,
)
from app.domain.constants import MECHANICAL_KEYBOARD_REFERENCE_CANDIDATES
from app.ports.search_port import SearchPort


KEYBOARD_TERMS = ("keyboard", "mechanical", "custom keyboard", "기계식", "키보드")
ACCESSORY_TERMS = (
    "keycap",
    "switch tester",
    "wrist rest",
    "desk mat",
    "artisan",
    "stabilizer",
    "pcb",
    "plate",
    "키캡",
    "스위치 테스터",
    "팜레스트",
    "데스크매트",
)
QUIET_TERMS = ("silent", "quiet", "저소음", "조용")
LOUD_TERMS = ("clicky", "blue switch", "loud", "청축")
LINEAR_TERMS = ("linear", "red switch", "적축")
TACTILE_TERMS = ("tactile", "brown switch", "갈축")
HOT_SWAP_TERMS = ("hot swap", "hotswap", "hot-swappable", "핫스왑")
FULL_SIZE_TERMS = ("full size", "full-size", "104", "108", "풀사이즈", "풀배열")


class SerpAPIAdapter(SearchPort):
    provider_name = "serpapi"
    mode = "configured"

    def __init__(
        self,
        api_key: str | None = None,
        engine: str = "google_shopping",
        expert_engine: str = "google",
        base_url: str = "https://serpapi.com/search.json",
        gl: str = "kr",
        hl: str = "ko",
        location: str | None = None,
        num: int = 6,
        google_domain: str = "google.com",
        device: str = "desktop",
        timeout_seconds: float = 20.0,
        shopping_adapter: ShoppingSearchAdapter | None = None,
        review_adapter: ReviewSearchAdapter | None = None,
    ) -> None:
        self._api_key = api_key
        self._commerce_engine = engine
        self._expert_engine = expert_engine
        self._base_url = base_url
        self._gl = gl
        self._hl = hl
        self._location = location
        self._num = num
        self._google_domain = google_domain
        self._device = device
        self._timeout_seconds = timeout_seconds
        self._shopping_adapter = shopping_adapter or ShoppingSearchAdapter()
        self._review_adapter = review_adapter or ReviewSearchAdapter()
        self._logger = logging.getLogger("supershopper.serpapi")

    def search_expert_signals(self, strategy: SearchStrategyPayload) -> list[ExpertSignalPayload]:
        if not self._api_key:
            self._logger.info("SerpAPI key missing, using mock expert signal fallback")
            return self._load_mock_expert_signals(strategy, reason="missing_api_key")

        try:
            signals = self._search_expert_signals_live(strategy)
        except Exception as exc:
            self._logger.warning("Expert signal retrieval failed, using mock fallback: %s", exc)
            return self._load_mock_expert_signals(strategy, reason="serpapi_error")

        if not signals:
            self._logger.warning("Expert signal retrieval returned no results, using mock fallback")
            return self._load_mock_expert_signals(strategy, reason="empty_live_results")

        self._logger.info("Expert signal retrieval success signal_count=%s", len(signals))
        return signals

    def verify_candidates(
        self,
        candidates: list[CandidateSeedPayload],
        strategy: SearchStrategyPayload,
    ) -> list[ProductPayload]:
        if not candidates:
            return []
        if not self._api_key:
            self._logger.info("SerpAPI key missing, using mock candidate verification fallback")
            return self._load_mock_products_for_candidates(candidates, strategy, reason="missing_api_key")

        try:
            products = self._verify_candidates_live(candidates, strategy)
        except Exception as exc:
            self._logger.warning("Candidate verification failed, using mock fallback: %s", exc)
            return self._load_mock_products_for_candidates(candidates, strategy, reason="serpapi_error")

        if not products:
            self._logger.warning("Candidate verification returned no products, using mock fallback")
            return self._load_mock_products_for_candidates(candidates, strategy, reason="empty_live_results")

        minimum_target = max(2, min(strategy.max_products, 3))
        if len(products) < minimum_target:
            self._logger.warning(
                "Live candidate verification was sparse product_count=%s supplementing_with_mock=%s",
                len(products),
                minimum_target - len(products),
            )
            products = self._supplement_with_mock_candidates(products, candidates, strategy, minimum_target)

        live_count = sum(1 for product in products if product.attributes.get("retrieval_source") == "serpapi_live")
        mock_count = len(products) - live_count
        self._logger.info(
            "Candidate verification success total_product_count=%s live_product_count=%s mock_product_count=%s",
            len(products),
            live_count,
            mock_count,
        )
        return products

    def search_reviews(
        self, products: list[ProductPayload], strategy: SearchStrategyPayload
    ) -> list[ProductPayload]:
        live_products = [self._ensure_live_evidence(product) for product in products if self._is_live_product(product)]
        mock_products = [product for product in products if not self._is_live_product(product)]

        enriched_mock = self._review_adapter.search_reviews(mock_products, strategy) if mock_products else []
        enriched_mock_by_id = {item.product_id: item for item in enriched_mock}

        combined: list[ProductPayload] = []
        live_products_by_id = {item.product_id: item for item in live_products}
        for product in products:
            if self._is_live_product(product):
                combined.append(live_products_by_id.get(product.product_id, product))
            else:
                combined.append(enriched_mock_by_id.get(product.product_id, product))
        return combined

    def _search_expert_signals_live(self, strategy: SearchStrategyPayload) -> list[ExpertSignalPayload]:
        deduped: dict[str, ExpertSignalPayload] = {}
        requested_limit = max(strategy.max_products * 2, 6)

        for query_index, search_query in enumerate(strategy.queries):
            response_payload = self._call_serpapi(
                search_query=search_query,
                num=requested_limit,
                engine=self._expert_engine,
            )
            organic_results = self._extract_organic_results(response_payload)
            self._logger.info(
                "Expert signal query success query_index=%s query=%s result_count=%s",
                query_index,
                search_query.query,
                len(organic_results),
            )
            for result_index, result in enumerate(organic_results):
                normalized = self._normalize_expert_signal(result, search_query, query_index, result_index)
                if normalized is None:
                    continue
                dedupe_key = normalized.url or normalized.title.lower()
                if dedupe_key not in deduped or normalized.confidence_score > deduped[dedupe_key].confidence_score:
                    deduped[dedupe_key] = normalized

        return sorted(
            deduped.values(),
            key=lambda item: item.confidence_score,
            reverse=True,
        )[:requested_limit]

    def _verify_candidates_live(
        self,
        candidates: list[CandidateSeedPayload],
        strategy: SearchStrategyPayload,
    ) -> list[ProductPayload]:
        verified_products: list[ProductPayload] = []
        requested_limit = max(strategy.max_products * 2, self._num, 6)

        for candidate in candidates:
            verification_query = self._build_candidate_verification_query(candidate)
            response_payload = self._call_serpapi(
                search_query=SearchQuery(query=verification_query, rationale="candidate verification"),
                num=requested_limit,
                engine=self._commerce_engine,
            )
            shopping_results = self._extract_shopping_results(response_payload)
            normalized_products: list[ProductPayload] = []
            for result_index, result in enumerate(shopping_results):
                normalized = self._normalize_shopping_result(
                    result=result,
                    search_query=SearchQuery(query=verification_query, rationale="candidate verification"),
                    query_index=0,
                    result_index=result_index,
                    candidate=candidate,
                )
                if normalized is not None:
                    normalized_products.append(normalized)

            if not normalized_products:
                continue

            best_product = sorted(
                normalized_products,
                key=lambda item: (item.relevance_score, item.trust_score),
                reverse=True,
            )[0]
            verified_products.append(best_product)

        return verified_products

    def _call_serpapi(
        self,
        search_query: SearchQuery,
        num: int,
        engine: str,
    ) -> dict:
        params = {
            "engine": engine,
            "q": search_query.query,
            "api_key": self._api_key,
            "google_domain": self._google_domain,
            "gl": self._gl,
            "hl": self._hl,
            "device": self._device,
            "num": num,
        }
        if self._location:
            params["location"] = self._location

        final_url = self._build_search_url(params)
        self._logger.info("Calling SerpAPI engine=%s final_url=%s", engine, final_url)

        http_request = request.Request(
            url=final_url,
            headers={"Accept": "application/json"},
            method="GET",
        )

        try:
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            self._logger.error("SerpAPI HTTP error status=%s detail=%s", exc.code, detail)
            raise RuntimeError(f"SerpAPI HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            self._logger.error("SerpAPI network error detail=%s", exc.reason)
            raise RuntimeError(f"SerpAPI network error: {exc.reason}") from exc

        if payload.get("error"):
            self._logger.error("SerpAPI API error detail=%s", payload["error"])
            raise RuntimeError(f"SerpAPI API error: {payload['error']}")

        return payload

    def _build_search_url(self, params: dict[str, object]) -> str:
        base = self._base_url.strip()
        if not base.startswith(("http://", "https://")):
            base = f"https://{base.lstrip('/')}"

        split_url = parse.urlsplit(base)
        path = split_url.path or "/search.json"
        existing_query = dict(parse.parse_qsl(split_url.query, keep_blank_values=True))
        existing_query.update({key: value for key, value in params.items() if value is not None})
        return parse.urlunsplit(
            (
                split_url.scheme or "https",
                split_url.netloc,
                path,
                parse.urlencode(existing_query),
                split_url.fragment,
            )
        )

    @staticmethod
    def _extract_organic_results(response_payload: dict) -> list[dict]:
        organic_results = response_payload.get("organic_results")
        if not isinstance(organic_results, list):
            return []
        return [item for item in organic_results if isinstance(item, dict)]

    @staticmethod
    def _extract_shopping_results(response_payload: dict) -> list[dict]:
        shopping_results = response_payload.get("shopping_results")
        if isinstance(shopping_results, list):
            return [item for item in shopping_results if isinstance(item, dict)]
        return []

    def _normalize_expert_signal(
        self,
        result: dict,
        search_query: SearchQuery,
        query_index: int,
        result_index: int,
    ) -> ExpertSignalPayload | None:
        title = self._first_text(result, "title")
        if not title:
            return None

        snippet = self._first_text(result, "snippet") or ""
        source = self._first_text(result, "source") or self._extract_domain(self._first_text(result, "link"))
        url = self._first_text(result, "link")
        combined_text = f"{title} {snippet} {search_query.query}".lower()
        if not self._looks_like_keyboard_signal(combined_text):
            return None

        mentioned_products = self._extract_mentioned_reference_products(combined_text)
        signal_type = self._infer_signal_type(combined_text)
        confidence_score = 0.45 + (0.18 if mentioned_products else 0.0)
        confidence_score += min(len(snippet) / 400.0, 0.18)
        confidence_score -= min(query_index * 0.03, 0.09)
        confidence_score -= min(result_index * 0.02, 0.12)

        signal_id_seed = url or title
        return ExpertSignalPayload(
            signal_id="signal:" + hashlib.sha1(signal_id_seed.encode("utf-8")).hexdigest()[:16],
            title=title,
            source=source or "serpapi-organic-result",
            snippet=snippet,
            url=url,
            signal_type=signal_type,
            mentioned_products=mentioned_products,
            confidence_score=round(max(confidence_score, 0.2), 3),
            retrieval_source="serpapi_live",
        )

    def _normalize_shopping_result(
        self,
        result: dict,
        search_query: SearchQuery,
        query_index: int,
        result_index: int,
        candidate: CandidateSeedPayload,
    ) -> ProductPayload | None:
        title = self._first_text(result, "title", "product_title", "name")
        if not title:
            return None

        descriptor_text = " ".join(
            [
                title,
                self._first_text(result, "snippet") or "",
                self._first_text(result, "source", "merchant", "store") or "",
                search_query.query,
            ]
        ).lower()
        if not self._looks_like_keyboard_signal(descriptor_text) or self._looks_like_accessory(descriptor_text):
            return None
        if not self._matches_candidate(descriptor_text, candidate):
            return None

        source = self._first_text(result, "source", "merchant", "store")
        url = self._first_text(result, "product_link", "link", "serpapi_link")
        price_display = self._first_text(result, "price")
        price = self._extract_price(result, price_display)
        rating = self._extract_float(result.get("rating"))
        review_count = self._extract_int(result.get("reviews"))
        delivery = self._first_text(result, "delivery")
        snippet = self._build_product_snippet(result, source, candidate)
        evidence = self._build_product_evidence(
            source=source,
            snippet=snippet,
            rating=rating,
            url=url,
            price_display=price_display,
            review_count=review_count,
            delivery=delivery,
        )

        product_id_seed = str(result.get("product_id") or url or candidate.name)
        product_id = "serpapi:" + hashlib.sha1(product_id_seed.encode("utf-8")).hexdigest()[:16]
        layout = self._infer_layout(descriptor_text) or candidate.inferred_layout
        switch_type = self._infer_switch_type(descriptor_text) or candidate.inferred_switch_type
        noise_level = self._infer_noise_level(descriptor_text, switch_type) or candidate.inferred_noise_level
        key_feel = self._infer_key_feel(switch_type)
        hot_swappable = self._infer_hot_swap(descriptor_text)
        connectivity = self._infer_connectivity(descriptor_text)

        return ProductPayload(
            product_id=product_id,
            name=candidate.name,
            brand=candidate.brand or self._infer_brand(title),
            price=price,
            currency=self._infer_currency(price_display),
            url=url,
            layout=layout,
            switch_type=switch_type,
            noise_level=noise_level,
            key_feel=key_feel,
            connectivity=connectivity,
            hot_swappable=hot_swappable,
            beginner_friendly=candidate.beginner_friendly,
            strengths=self._build_strengths(layout, switch_type, noise_level, hot_swappable, source),
            cautions=self._build_cautions(layout, switch_type, noise_level, price_display),
            evidence_summary=[item.snippet for item in evidence[:2]],
            attributes={
                "seller": source,
                "price_display": price_display,
                "query": search_query.query,
                "delivery": delivery,
                "review_count": review_count,
                "retrieval_source": "serpapi_live",
                "verification_query": search_query.query,
                "candidate_id": candidate.candidate_id,
                "candidate_generation_reason": candidate.generation_reason,
            },
            evidence=evidence,
            relevance_score=self._estimate_relevance(
                descriptor_text=descriptor_text,
                query_index=query_index,
                result_index=result_index,
                rating=rating,
                review_count=review_count,
            ),
            trust_score=self._estimate_trust_score(
                rating=rating,
                review_count=review_count,
                has_url=bool(url),
                evidence_count=len(evidence),
            ),
        )

    def _build_product_evidence(
        self,
        source: str | None,
        snippet: str,
        rating: float | None,
        url: str | None,
        price_display: str | None,
        review_count: int | None,
        delivery: str | None,
    ) -> list[ReviewSnippet]:
        evidence = [
            ReviewSnippet(
                source=source or "serpapi-shopping-result",
                snippet=snippet,
                rating=rating,
                url=url,
            )
        ]
        seller_summary_parts: list[str] = []
        if source:
            seller_summary_parts.append(f"seller {source}")
        if price_display:
            seller_summary_parts.append(f"price {price_display}")
        if review_count is not None:
            seller_summary_parts.append(f"reviews {review_count}")
        if delivery:
            seller_summary_parts.append(f"delivery {delivery}")
        if seller_summary_parts:
            evidence.append(
                ReviewSnippet(
                    source=source or "serpapi-shopping-result",
                    snippet=" / ".join(seller_summary_parts),
                    rating=rating,
                    url=url,
                )
            )
        return evidence

    @staticmethod
    def _first_text(payload: dict, *keys: str) -> str | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _extract_price(result: dict, price_display: str | None) -> float | None:
        extracted_price = result.get("extracted_price")
        if isinstance(extracted_price, (int, float)):
            return float(extracted_price)
        if not price_display:
            return None
        match = re.search(r"(\d[\d,]*(?:\.\d+)?)", price_display)
        if not match:
            return None
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None

    @staticmethod
    def _extract_float(value: object) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", "").strip())
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            match = re.search(r"\d[\d,]*", value)
            if match:
                return int(match.group(0).replace(",", ""))
        return None

    @staticmethod
    def _extract_domain(url: str | None) -> str | None:
        if not url:
            return None
        parsed = parse.urlsplit(url)
        return parsed.netloc or None

    @staticmethod
    def _looks_like_keyboard_signal(text: str) -> bool:
        return any(keyword in text for keyword in KEYBOARD_TERMS)

    @staticmethod
    def _looks_like_accessory(text: str) -> bool:
        return any(keyword in text for keyword in ACCESSORY_TERMS)

    @staticmethod
    def _infer_signal_type(text: str) -> str:
        if any(keyword in text for keyword in ("best", "추천", "top", "vs", "compare", "비교")):
            return "comparison"
        if any(keyword in text for keyword in ("review", "리뷰", "후기")):
            return "review"
        return "guide"

    @staticmethod
    def _extract_mentioned_reference_products(text: str) -> list[str]:
        mentioned: list[str] = []
        for reference in MECHANICAL_KEYBOARD_REFERENCE_CANDIDATES:
            if any(alias in text for alias in reference["aliases"]):
                mentioned.append(reference["name"])
        return mentioned

    @staticmethod
    def _build_candidate_verification_query(candidate: CandidateSeedPayload) -> str:
        base = candidate.name
        switch_hint = candidate.inferred_switch_type.replace("_", " ") if candidate.inferred_switch_type else "keyboard"
        return f"{base} mechanical keyboard {switch_hint}"

    @staticmethod
    def _matches_candidate(descriptor_text: str, candidate: CandidateSeedPayload) -> bool:
        normalized_name = candidate.name.lower()
        normalized_brand = (candidate.brand or "").lower()
        normalized_tokens = [token for token in normalized_name.split() if len(token) > 2]
        if normalized_name in descriptor_text:
            return True
        if normalized_brand and normalized_brand in descriptor_text:
            token_matches = sum(1 for token in normalized_tokens if token in descriptor_text)
            return token_matches >= 1
        return any(token in descriptor_text for token in normalized_tokens[:2])

    @staticmethod
    def _is_live_product(product: ProductPayload) -> bool:
        return product.attributes.get("retrieval_source") == "serpapi_live"

    @staticmethod
    def _infer_brand(title: str) -> str | None:
        tokens = title.split()
        return tokens[0] if tokens else None

    @staticmethod
    def _infer_currency(price_display: str | None) -> str:
        if not price_display:
            return "KRW"
        normalized = price_display.lower()
        if "₩" in price_display or "원" in price_display or "krw" in normalized:
            return "KRW"
        if "$" in price_display or "usd" in normalized:
            return "USD"
        return "KRW"

    @staticmethod
    def _infer_layout(text: str) -> str | None:
        if "75%" in text or "75배열" in text:
            return "75%"
        if "tkl" in text or "tenkeyless" in text or "텐키리스" in text:
            return "TKL"
        if any(keyword in text for keyword in FULL_SIZE_TERMS):
            return "full_size"
        return None

    @staticmethod
    def _infer_switch_type(text: str) -> str | None:
        if any(keyword in text for keyword in QUIET_TERMS) and any(keyword in text for keyword in TACTILE_TERMS):
            return "silent_tactile"
        if any(keyword in text for keyword in QUIET_TERMS) and any(keyword in text for keyword in LINEAR_TERMS):
            return "silent_linear"
        if any(keyword in text for keyword in LOUD_TERMS):
            return "clicky"
        if any(keyword in text for keyword in TACTILE_TERMS):
            return "tactile"
        if any(keyword in text for keyword in LINEAR_TERMS):
            return "linear"
        return None

    @staticmethod
    def _infer_noise_level(text: str, switch_type: str | None) -> str | None:
        if any(keyword in text for keyword in QUIET_TERMS):
            return "quiet"
        if switch_type == "clicky" or any(keyword in text for keyword in LOUD_TERMS):
            return "loud"
        if switch_type is not None:
            return "moderate"
        return None

    @staticmethod
    def _infer_key_feel(switch_type: str | None) -> str | None:
        mapping = {
            "silent_linear": "smooth_linear",
            "silent_tactile": "light_tactile",
            "linear": "smooth_linear",
            "tactile": "light_tactile",
            "clicky": "sharp_clicky",
        }
        return mapping.get(switch_type)

    @staticmethod
    def _infer_hot_swap(text: str) -> bool | None:
        if any(keyword in text for keyword in HOT_SWAP_TERMS):
            return True
        if "solder" in text or "납땜" in text:
            return False
        return None

    @staticmethod
    def _infer_connectivity(text: str) -> list[str]:
        connectivity: list[str] = []
        if "bluetooth" in text or "블루투스" in text:
            connectivity.append("bluetooth")
        if "2.4g" in text or "2.4 ghz" in text:
            connectivity.append("2.4g")
        if "wireless" in text or "무선" in text:
            connectivity.append("wireless")
        if "wired" in text or "유선" in text:
            connectivity.append("wired")
        return connectivity

    @staticmethod
    def _build_product_snippet(
        result: dict,
        source: str | None,
        candidate: CandidateSeedPayload,
    ) -> str:
        snippet = SerpAPIAdapter._first_text(result, "snippet")
        if snippet:
            return snippet
        parts = [candidate.name]
        if source:
            parts.append(f"seller {source}")
        price = SerpAPIAdapter._first_text(result, "price")
        if price:
            parts.append(f"price {price}")
        delivery = SerpAPIAdapter._first_text(result, "delivery")
        if delivery:
            parts.append(f"delivery {delivery}")
        return " / ".join(parts)

    @staticmethod
    def _build_strengths(
        layout: str | None,
        switch_type: str | None,
        noise_level: str | None,
        hot_swappable: bool | None,
        source: str | None,
    ) -> list[str]:
        strengths: list[str] = []
        if noise_level == "quiet":
            strengths.append("저소음 성향으로 공용 공간에서도 부담이 적습니다.")
        if layout == "75%":
            strengths.append("75% 배열이라 방향키를 유지하면서 공간을 줄이기 쉽습니다.")
        if layout == "TKL":
            strengths.append("텐키리스 배열이라 입문자가 적응하기 쉬운 편입니다.")
        if switch_type in {"silent_linear", "silent_tactile"}:
            strengths.append("입문자용 저소음 조건과 잘 맞는 스위치 계열로 보입니다.")
        if hot_swappable:
            strengths.append("핫스왑 지원으로 나중에 스위치를 바꾸기 편할 수 있습니다.")
        if source:
            strengths.append(f"실제 판매처 정보가 검색 결과에 노출되었습니다: {source}.")
        return strengths[:3]

    @staticmethod
    def _build_cautions(
        layout: str | None,
        switch_type: str | None,
        noise_level: str | None,
        price_display: str | None,
    ) -> list[str]:
        cautions: list[str] = []
        if layout == "full_size":
            cautions.append("풀배열이라 75%나 텐키리스보다 책상 공간을 더 차지합니다.")
        if switch_type == "clicky" or noise_level == "loud":
            cautions.append("현재 요청의 저소음 조건과는 다를 수 있습니다.")
        if not price_display:
            cautions.append("쇼핑 결과에서 가격 문자열이 명확하지 않았습니다.")
        return cautions[:3]

    @staticmethod
    def _estimate_relevance(
        descriptor_text: str,
        query_index: int,
        result_index: int,
        rating: float | None,
        review_count: int | None,
    ) -> float:
        score = 0.48
        if any(keyword in descriptor_text for keyword in QUIET_TERMS):
            score += 0.15
        if "75%" in descriptor_text or "tkl" in descriptor_text or "텐키리스" in descriptor_text:
            score += 0.08
        if any(keyword in descriptor_text for keyword in HOT_SWAP_TERMS):
            score += 0.05
        if rating is not None:
            score += min(rating / 20.0, 0.20)
        if review_count:
            score += min(review_count / 500.0, 0.08)
        score -= min(query_index * 0.03, 0.09)
        score -= min(result_index * 0.02, 0.14)
        return round(max(score, 0.25), 3)

    @staticmethod
    def _estimate_trust_score(
        rating: float | None,
        review_count: int | None,
        has_url: bool,
        evidence_count: int,
    ) -> float:
        score = 0.12
        if has_url:
            score += 0.08
        if evidence_count:
            score += min(evidence_count * 0.07, 0.14)
        if rating is not None:
            score += min(rating / 10.0, 0.35)
        if review_count:
            score += min(review_count / 1000.0, 0.16)
        return round(min(score, 0.92), 3)

    def _ensure_live_evidence(self, product: ProductPayload) -> ProductPayload:
        if product.evidence:
            return product
        fallback_evidence = [
            ReviewSnippet(
                source=str(product.attributes.get("seller") or "serpapi-shopping-result"),
                snippet="실시간 쇼핑 검색 결과 기반으로 검증된 후보입니다.",
                rating=None,
                url=product.url,
            )
        ]
        return product.model_copy(
            update={
                "evidence": fallback_evidence,
                "evidence_summary": [item.snippet for item in fallback_evidence],
                "trust_score": max(product.trust_score, 0.3),
            }
        )

    def _load_mock_expert_signals(
        self,
        strategy: SearchStrategyPayload,
        reason: str,
    ) -> list[ExpertSignalPayload]:
        del strategy
        signals = [
            ExpertSignalPayload(
                signal_id="mock-signal-keymellow",
                title="입문용 저소음 기계식 키보드 추천",
                source="mock-expert-guide",
                snippet="KeyMellow 75 Flex와 LumaKeys Flow TKL이 처음 쓰기 무난한 저소음 후보로 자주 언급됩니다.",
                url=None,
                signal_type="comparison",
                mentioned_products=["KeyMellow 75 Flex", "LumaKeys Flow TKL"],
                confidence_score=0.71,
                retrieval_source="mock_expert_signal_fallback",
                fallback_reason=reason,
            ),
            ExpertSignalPayload(
                signal_id="mock-signal-monotype",
                title="사무용 기계식 키보드 배열 비교",
                source="mock-layout-guide",
                snippet="숫자패드가 꼭 필요하면 MonoType Office 98 같은 풀배열 후보를 보되, 대부분은 75%나 텐키리스가 더 무난합니다.",
                url=None,
                signal_type="guide",
                mentioned_products=["MonoType Office 98"],
                confidence_score=0.64,
                retrieval_source="mock_expert_signal_fallback",
                fallback_reason=reason,
            ),
        ]
        self._logger.info(
            "Using mock expert signal fallback reason=%s signal_count=%s",
            reason,
            len(signals),
        )
        return signals

    def _load_mock_products_for_candidates(
        self,
        candidates: list[CandidateSeedPayload],
        strategy: SearchStrategyPayload,
        reason: str,
    ) -> list[ProductPayload]:
        catalog_products = self._shopping_adapter.search_products(strategy)
        lowered_candidate_names = {candidate.name.lower() for candidate in candidates}
        filtered = [
            product.model_copy(
                update={
                    "attributes": {
                        **product.attributes,
                        "retrieval_source": "mock_catalog_fallback",
                        "fallback_reason": reason,
                    }
                }
            )
            for product in catalog_products
            if product.name.lower() in lowered_candidate_names
        ]
        if not filtered:
            filtered = [
                product.model_copy(
                    update={
                        "attributes": {
                            **product.attributes,
                            "retrieval_source": "mock_catalog_fallback",
                            "fallback_reason": reason,
                        }
                    }
                )
                for product in catalog_products
            ]
        self._logger.info(
            "Using mock candidate verification fallback reason=%s product_count=%s",
            reason,
            len(filtered),
        )
        return filtered

    def _supplement_with_mock_candidates(
        self,
        live_products: list[ProductPayload],
        candidates: list[CandidateSeedPayload],
        strategy: SearchStrategyPayload,
        minimum_target: int,
    ) -> list[ProductPayload]:
        supplemented = list(live_products)
        existing_names = {product.name.lower() for product in live_products}
        for mock_product in self._load_mock_products_for_candidates(
            candidates=candidates,
            strategy=strategy,
            reason="supplement_sparse_live_results",
        ):
            if mock_product.name.lower() in existing_names:
                continue
            supplemented.append(mock_product)
            existing_names.add(mock_product.name.lower())
            if len(supplemented) >= minimum_target:
                break
        return supplemented


class MockSearchAdapter(SerpAPIAdapter):
    provider_name = "mock-search"
    mode = "mock"

    def search_expert_signals(self, strategy: SearchStrategyPayload) -> list[ExpertSignalPayload]:
        self._logger.info("Using mock search provider for expert signals")
        return self._load_mock_expert_signals(strategy, reason="mock_provider_selected")

    def verify_candidates(
        self,
        candidates: list[CandidateSeedPayload],
        strategy: SearchStrategyPayload,
    ) -> list[ProductPayload]:
        self._logger.info("Using mock search provider for candidate verification")
        return self._load_mock_products_for_candidates(
            candidates=candidates,
            strategy=strategy,
            reason="mock_provider_selected",
        )

    def search_reviews(
        self, products: list[ProductPayload], strategy: SearchStrategyPayload
    ) -> list[ProductPayload]:
        self._logger.info("Using mock review enrichment for retrieval")
        enriched_products = self._review_adapter.search_reviews(products, strategy)
        return [
            product.model_copy(
                update={
                    "attributes": {
                        **product.attributes,
                        "retrieval_source": product.attributes.get(
                            "retrieval_source",
                            "mock_catalog_fallback",
                        ),
                    }
                }
            )
            for product in enriched_products
        ]
