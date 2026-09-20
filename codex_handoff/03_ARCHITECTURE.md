# Architecture

## 핵심 원칙

LLM에게 "할인 찾아줘" 한 번 호출하고 결과를 그대로 보여주지 않는다.

파이프라인: 1. Query Parser 2. Search Planner 3. Parallel Web Search 4.
Benefit Extraction / Normalization 5. Verification 6. Eligibility Engine
7. Base Price Resolver 8. Price Calculator 9. Deduplication / Ranking
10. API Response

## 책임

### LLM

-   자연어 의도 구조화
-   검색 계획 생성
-   웹의 비정형 할인 조건을 구조화된 JSON으로 추출
-   필요한 경우 source 간 정보 정리

### 일반 코드

-   schema validation
-   명확한 eligibility rule evaluation
-   가격 계산
-   정렬
-   중복 제거
-   상태 관리

## PoC 권장 구조

처음에는 OpenAI Responses API + web search capability로 end-to-end
가능성을 먼저 검증한다.

안정성이 부족할 경우 검색 계층을 분리한다: Search Planner → Search API →
URL 후보 → Content extraction → LLM normalization.

검색 제공자는 교체 가능하도록 adapter/interface로 감싼다.

## Query Parser

입력: `이번 주 토요일 에버랜드 갈 거야`

출력: - merchant - product - date - location - quantity

알 수 없는 값은 null. 불필요한 추측 금지.

## Search Planner

입력: - PurchaseIntent - UserProfile - current date

출력: 독립 실행 가능한 SearchTask 최대 8개.

Personal: - card - carrier - membership - age - occupation - location

Discovery: - merchant promotion - current promotion / payment / coupon /
partnership

## Search

SearchTask들은 가능한 한 병렬 처리한다.

공식 source 우선순위: 1. merchant official 2. benefit provider official
3. official partner 4. reliable secondary 5. blog/community는 보조 증거

검색 snippet만으로 확정하지 않는다.

## Benefit Extraction

반드시 추출할 수 있는 것만 구조화한다. 중요 필드: - title - provider -
merchant - category - discount - requirements - validFrom/validUntil -
purchaseMethod - stackable - source - confidence

페이지에 없는 조건/할인율을 추론하지 않는다.

## Eligibility

Benefit requirements와 UserProfile 비교.

결과: - confirmed - needs_info - not_eligible

`needs_info`일 때 missing field와 사용자 질문을 생성할 수 있어야 한다.

## Base Price

할인 계산 전 공식 정가/대상 가격을 별도로 확인한다. 날짜/상품/연령 구분
등이 있으면 price context에 포함한다.

## Price Calculation

LLM 사용 금지. - percentage - fixed - special_price

불확실한 discount는 계산하지 않는다.

## Deduplication

동일 혜택이 여러 source에서 발견될 수 있다. provider + merchant +
discount + valid period 등을 이용해 후보를 묶고 공식 source를 대표로
선택한다.

## 향후 할인 조합

MVP 후순위. stackability가 확실히 검증된 혜택만 조합 가능. 불명확하면
조합하지 않는다.
