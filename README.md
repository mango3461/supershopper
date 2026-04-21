# 실시간 정보 기반 탐색 보조 AI

실시간 검색 결과를 바탕으로, 낯선 상품 분야를 사용자가 덜 힘들게 이해하고 선택할 수 있도록 돕는 탐색 보조 AI 프로젝트입니다.

## 프로젝트 개요

이 프로젝트는 사용자가 새로운 분야의 상품을 탐색할 때 겪는 정보 과부하와 비교 피로를 줄이기 위해 설계되었습니다.  
최신성과 사실성은 검색 API가 담당하고, LLM은 검색 전략 수립과 결과 해석, 사용자 맞춤형 요약에 집중합니다.

## 설계 철학 (Core Principles)

- **검색 중심 (Retrieval-First)**
  - 사실 관계와 최신성(가격, 재고, 트렌드)은 검색 API가 책임집니다.
  - 시스템은 최신 시장 정보에 대한 판단을 내부 모델 지식이 아니라 검색 결과에 기반해 수행합니다.

- **LLM 보조 (LLM-as-Interpreter)**
  - LLM은 검색 전략 수립, 결과 해석, 사용자 맞춤형 요약에 집중합니다.
  - 최신 정보를 단정하는 역할보다는, 수집된 정보를 이해 가능한 선택지로 바꾸는 역할을 맡습니다.

- **워크플로우 구조 (Workflow-Oriented)**
  - 자유 대화가 아닌 `[의도 -> 검색 -> 필터 -> 요약 -> 추천]`의 엄격한 파이프라인을 따릅니다.
  - 각 단계는 명확한 책임을 가지며, 독립적으로 테스트 가능해야 합니다.

- **인지 부담 감소 (Cognitive Load Reduction)**
  - 단순한 검색 결과 나열을 지양합니다.
  - 사용자가 더 쉽게 결정할 수 있도록 정보를 압축하고, 비교 기준과 추천 근거를 함께 제공합니다.

## 폴더 구조 (Tree)

```text
backend/

├── app/

│   ├── main.py

│   ├── api/

│   │   ├── routes/

│   │   │   ├── chat.py

│   │   │   ├── recommend.py

│   │   │   └── health.py

│   │   ├── schemas/

│   │   │   ├── request.py

│   │   │   ├── response.py

│   │   │   └── common.py

│   │   └── dependencies.py

│   │

│   ├── orchestrators/

│   │   └── shopping_flow.py

│   │

│   ├── domain/

│   │   ├── models/

│   │   │   ├── user_need.py

│   │   │   ├── search_strategy.py

│   │   │   ├── product_candidate.py

│   │   │   ├── review_evidence.py

│   │   │   └── recommendation.py

│   │   ├── policies/

│   │   │   ├── ranking_policy.py

│   │   │   ├── confidence_policy.py

│   │   │   └── presentation_policy.py

│   │   └── constants.py

│   │

│   ├── usecases/

│   │   ├── analyze_intent.py

│   │   ├── build_search_strategy.py

│   │   ├── retrieve_products.py

│   │   ├── filter_evidence.py

│   │   ├── summarize_results.py

│   │   ├── compare_candidates.py

│   │   └── generate_recommendation.py

│   │

│   ├── ports/

│   │   ├── llm_port.py

│   │   ├── search_port.py

│   │   ├── cache_port.py

│   │   └── logger_port.py

│   │

│   ├── adapters/

│   │   ├── llm/

│   │   │   ├── openai_adapter.py

│   │   │   └── gemini_adapter.py

│   │   ├── search/

│   │   │   ├── serpapi_adapter.py

│   │   │   ├── shopping_search_adapter.py

│   │   │   └── review_search_adapter.py

│   │   ├── cache/

│   │   │   └── redis_adapter.py

│   │   └── logging/

│   │       └── app_logger.py

│   │

│   ├── prompts/

│   │   ├── intent_prompt.py

│   │   ├── strategy_prompt.py

│   │   ├── summary_prompt.py

│   │   └── recommendation_prompt.py

│   │

│   ├── services/

│   │   ├── ranking_service.py

│   │   ├── trust_service.py

│   │   └── response_formatter.py

│   │

│   ├── infra/

│   │   ├── config.py

│   │   ├── settings.py

│   │   └── container.py

│   │

│   └── tests/

│       ├── unit/

│       └── integration/

│

├── .env

├── requirements.txt

└── README.md
```
