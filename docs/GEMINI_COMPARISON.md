# OpenAI / Gemini live 비교 · 2026-09-20

비교 실행은 `에버랜드`와 문서의 mock profile을 입력으로 사용했습니다. API 키 값과 SDK 원문 오류는 기록하지 않았습니다. 각 provider를 fixture로 대체하지 않았습니다.

## 실제 실행 결과

| 기준                                            | OpenAI Provider                                                                                                                      | Gemini Provider                                                                                                                                                                          |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 설정                                            | `SEARCH_PROVIDER=openai`                                                                                                             | `SEARCH_PROVIDER=gemini`                                                                                                                                                                 |
| 모델                                            | `gpt-5-mini`                                                                                                                         | `gemini-2.5-flash`                                                                                                                                                                       |
| API 구조                                        | Responses API `responses.parse`로 intent/plan, Responses `web_search`로 task별 검색, citations URL 본문 재조회, Zod BenefitCandidate | `@google/genai` `models.generateContent`, intent/plan JSON schema, task별 `googleSearch` grounding, grounding proxy URL을 최종 URL로 follow 후 본문 재조회, JSON 후 Zod BenefitCandidate |
| intent                                          | 실패                                                                                                                                 | 첫 실행 성공(약 2.9초). 재실행은 quota 429                                                                                                                                               |
| search plan                                     | 실행 도달 전 실패                                                                                                                    | 첫 실행 성공(약 7.8초)                                                                                                                                                                   |
| 실제 Google/OpenAI 웹 검색                      | 실행되지 않음. intent 단계에서 HTTP 429 quota/billing                                                                                | 첫 실행에서 grounding search 7개 task 호출. task별 3~4개 Google 검색 query가 관찰됨                                                                                                      |
| 공식 출처 수                                    | 0                                                                                                                                    | 첫 실행에서 공식 최종 URL 5개가 확인됨. URL: 현대카드 3개, SKT 멤버십 1개가 audit에 남았고 한 현대카드 magazine URL이 중복됨                                                             |
| BenefitCandidate                                | 0                                                                                                                                    | 0. 첫 실행에서 한 task가 출처 본문을 읽었지만 Gemini 2.5의 structured schema 제약으로 추출 호출이 HTTP 400. 이후 JSON-text 후 Zod 검증 방식으로 수정했으나 quota가 소진되어 재검증 불가  |
| confirmed / needs_info / not_eligible / unknown | 0 / 0 / 0 / 0                                                                                                                        | 0 / 0 / 0 / 0. 후보가 schema 검증까지 도달하지 않음                                                                                                                                      |
| 조건 누락                                       | 평가 불가                                                                                                                            | 후보 미생성으로 평가 불가. 공식 본문 재조회와 `verifyBenefit`은 연결됨                                                                                                                   |
| 유효기간                                        | 확인하지 못함                                                                                                                        | 후보 미생성으로 확인하지 못함                                                                                                                                                            |
| base price                                      | 확인하지 못함                                                                                                                        | 입력 intent에 방문일·정확한 상품·수량이 없어 deterministic resolver가 의도적으로 null 반환                                                                                               |
| 내 가격                                         | 계산하지 않음                                                                                                                        | 계산하지 않음                                                                                                                                                                            |
| 응답 시간                                       | 약 0.9~2.3초 후 intent 429                                                                                                           | 성공한 첫 intent/plan + task 검색 전체 약 30초. task별 약 7~10초. 재시도 첫 intent 429                                                                                                   |

## 발견한 공식 출처

Gemini grounding이 반환한 proxy citation은 그대로 공식 출처로 신뢰하지 않고 redirect 후 최종 HTTPS 호스트를 확인했습니다. 확인된 URL은 다음과 같습니다.

- 현대카드 이벤트: `https://card.hyundaicard.com/EVENT?id=zero_4&eventCode=CPHJS`
- 현대카드 혜택: `https://www.hyundaicard.com/cpb/ev/CPBEV0101_06.hc?bnftWebEvntCd=GZK825`
- 현대카드 에버랜드 안내: `https://card.hyundaicard.com/magazine/...hdc`
- SKT 멤버십 브랜드: `https://sktmembership.tworld.co.kr/mps/pc-bff/benefitbrand/detail.do?brandId=5244`

이 출처의 숫자·기간·조건을 BenefitCandidate로 확정하지 않았습니다. 본문 인용이 schema에 맞고 실제 HTML 원문에서 다시 검증되어야만 후보가 표시됩니다.

## 문제와 다음 검증

- Gemini 2.5는 Google Search tool과 복잡한 `responseSchema`를 함께 사용하는 extraction 요청에서 HTTP 400을 반환했습니다. 현재 구현은 Grounding 검색과 JSON text 응답을 분리하고, JSON을 Zod로 검증하도록 변경했습니다. 이는 다음 quota 복구 후 확인해야 합니다.
- Google Search Grounding은 한 task에서 여러 검색 query를 실행할 수 있고 task를 병렬 실행하면 quota를 빠르게 소모합니다. 비교 실행은 실제로 7 task를 실행했으며 quota/billing 429가 발생했습니다. 이후에는 비교 모드에서 task 수·동시성을 낮추거나 순차 실행하는 것이 우선입니다.
- OpenAI도 동일 환경에서 intent 첫 요청이 quota/billing 429로 거절되어 OpenAI 후보를 만들지 못했습니다. 그러므로 “Gemini가 할인 후보를 더 잘 찾았다”는 품질 결론은 내릴 수 없습니다.
- fixture fallback은 없습니다. quota/400/본문 검증 실패는 task 실패 또는 빈 결과로 남습니다.
