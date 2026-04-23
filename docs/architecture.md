# Architecture

## 아키텍처 패턴

이 프로젝트는 **헥사고날(Hexagonal) + 클린 아키텍처**를 기반으로 설계됩니다.  
핵심 목표는 외부 의존성(LLM API, 검색 API, 캐시, 로깅)을 비즈니스 로직으로부터 분리하고, 워크플로우 중심의 안정적인 탐색 보조 시스템을 구축하는 것입니다.

### 왜 이 패턴을 선택했는가

- 검색 API와 LLM API는 언제든 교체될 수 있습니다.
- 최신성과 사실성은 외부 소스에 의존하므로 외부 연동 계층의 독립성이 중요합니다.
- 비즈니스 로직은 특정 제공자(OpenAI, Gemini, SerpAPI 등)에 종속되지 않아야 합니다.
- 단계형 워크플로우를 명확하게 분리해야 테스트와 디버깅이 쉬워집니다.

## 핵심 구성 요소

### Domain
- 핵심 비즈니스 로직과 모델을 담습니다.
- 외부 의존성이 전혀 없어야 합니다.
- 예:
  - `UserNeed`
  - `SearchStrategy`
  - `ProductCandidate`
  - `ReviewEvidence`
  - `Recommendation`

### Ports
- 외부 세계와 통신하기 위한 인터페이스 계층입니다.
- 추상 클래스 또는 프로토콜 형태로 정의합니다.
- 예:
  - `LLMPort`
  - `SearchPort`
  - `CachePort`
  - `LoggerPort`

### Adapters
- Ports의 실제 구현체입니다.
- 외부 API와 직접 통신합니다.
- 예:
  - `OpenAIAdapter`
  - `GeminiAdapter`
  - `SerpAPIAdapter`
  - `RedisAdapter`

### Orchestrator
- 전체 워크플로우 단계를 순차적으로 실행하고 상태를 관리합니다.
- 각 use case를 올바른 순서로 호출하고, 실패 시 재시도나 대체 전략을 제어할 수 있습니다.
- 예:
  - `shopping_flow.py`

## 디렉토리 구조

아래 구조는 프로젝트의 기준 구조이며, 그대로 유지합니다.

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

## 단계별 모듈 명세 (Workflow Specification)

전체 워크플로우는 다음의 순서를 따릅니다.

`Intent Analysis -> Search Strategy -> Expert Signal Retrieval -> Candidate Generation -> Commerce Retrieval -> Evidence Filtering -> Summarization -> Recommendation`

### 1. Intent Analysis
- 질문에서 `category`, `user_level`, `budget`, `constraints`를 추출합니다.
- 자유 자연어를 구조화된 니즈로 바꿉니다.
- 초보자 여부와 핵심 구매 기준을 파악합니다.

### 2. Search Strategy
- 추출된 의도를 바탕으로 검색 쿼리 3~5개를 생성합니다.
- 사용자가 직접 검색어를 모르더라도 적절한 탐색 경로를 만듭니다.

### 3. Expert Signal Retrieval
- 상품 자체가 아니라 추천, 가이드, 비교 콘텐츠를 먼저 수집합니다.
- 전문가 또는 고수의 판단이 반영된 정보를 기반으로 후보군 생성을 준비합니다.
- 단순 검색 결과가 아니라 추천 패턴 기반의 신호를 추출합니다.

### 4. Candidate Generation
- Expert Signal Retrieval 단계에서 수집된 정보를 바탕으로 추천되는 모델을 추출합니다.
- 이 단계에서 실제 구매 후보군이 결정됩니다.
- 이후 단계는 이 후보군을 검증하는 역할을 수행합니다.

### 5. Commerce Retrieval
- 이 단계는 후보군을 생성하는 것이 아니라, 이미 선택된 후보군의 구매 가능성을 검증하는 역할을 합니다.
- 가격, 판매처, 배송, 후기 등 실제 구매에 필요한 정보를 수집합니다.
- 최신성과 사실성은 이 단계가 책임집니다.

### 6. Evidence Filtering
- 중복/광고/노이즈를 제거하고 신뢰도 점수를 부여합니다.
- 후속 요약과 추천에 사용할 정제된 근거 데이터를 만듭니다.

### 7. Summarization
- 도메인 지식이 없는 사용자를 위해 핵심 구매 기준을 요약합니다.
- 수집된 근거의 핵심 장단점을 초보자 관점에서 단순화합니다.

### 8. Recommendation
- 최종 후보 2~3개를 선정합니다.
- 각 후보가 왜 적합한지 비교 근거와 함께 설명합니다.

## 구현 규칙 (Implementation Rules)

### 데이터 교환 규칙
- 모든 데이터 교환은 `api/schemas/`에 정의된 Pydantic 모델을 사용합니다.
- request/response 및 모듈 간 전달 포맷을 명확히 고정합니다.
- 암묵적인 dict 전달을 최소화하고 스키마 기반 검증을 우선합니다.

### 의존성 규칙
- 비즈니스 로직(`usecases/`)은 특정 어댑터(OpenAI 등)에 직접 의존하지 않습니다.
- 반드시 `ports/`의 인터페이스를 통해 외부 기능을 사용합니다.
- 외부 구현체는 `adapters/`에만 존재해야 합니다.

### 프롬프트 관리 규칙
- 프롬프트는 코드 내에 하드코딩하지 않습니다.
- `prompts/` 폴더에서 중앙 관리합니다.
- 프롬프트 변경이 비즈니스 로직 수정으로 이어지지 않도록 분리합니다.

### 의존성 주입 규칙
- FastAPI의 Dependency Injection을 활용하여 어댑터를 주입합니다.
- 라우터와 유스케이스는 직접 구현체를 생성하지 않습니다.
- 구현체 선택은 `dependencies.py` 또는 `infra/container.py`에서 관리합니다.

### 책임 분리 규칙
- `api/`는 입출력 처리에 집중합니다.
- `orchestrators/`는 전체 흐름 제어에 집중합니다.
- `usecases/`는 단계별 비즈니스 동작을 담당합니다.
- `domain/`은 핵심 모델과 정책을 유지합니다.
- `adapters/`는 외부 시스템 연동만 담당합니다.

### 테스트 규칙
- `tests/unit/`에서는 use case와 domain 정책을 단위 테스트합니다.
- `tests/integration/`에서는 orchestrator와 adapter 조합을 통합 테스트합니다.
- 외부 API 호출은 테스트에서 mock 또는 stub으로 대체합니다.
