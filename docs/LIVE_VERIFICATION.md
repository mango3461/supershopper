# OpenAI live 연결 검증 · 2026-09-20

## 결과

실제 OpenAI API에 요청을 보냈지만 의도 분석 첫 단계에서 HTTP 429로 거절되었습니다. 따라서 이번 실행은 **live 파이프라인 성공 검증이 아닙니다**.

| 항목                           | 이번 실제 실행 결과                                                                    |
| ------------------------------ | -------------------------------------------------------------------------------------- |
| 입력                           | `에버랜드`, 문서의 초기 mock **프로필** 사용. 검색 결과 fixture는 사용하지 않음        |
| Provider                       | `openai-web-search` (`.env.local`의 `SEARCH_PROVIDER`를 `openai`로 변경)               |
| 요청 모델                      | `gpt-5-mini`                                                                           |
| API                            | OpenAI Responses API, `POST /v1/responses`, `responses.parse` + Zod Structured Outputs |
| 최초 요청 단계                 | `purchase_intent`                                                                      |
| 응답                           | HTTP 429, SDK `RateLimitError`                                                         |
| 안전한 원인 분류               | `quota_or_billing` — 응답 내용의 사용 한도/결제 관련 표현만 분류. 원문은 기록하지 않음 |
| 성공 응답의 실제 모델 snapshot | 성공 응답이 없어 확인 불가                                                             |
| 실제 웹 검색 호출              | 미실행. 의도 분석이 거절되어 검색 단계에 도달하지 않음                                 |
| 실제 검색된 공식 출처          | 없음                                                                                   |
| BenefitCandidate               | 추출되지 않음                                                                          |
| eligibility                    | 평가할 후보가 없어 미실행                                                              |
| base price                     | 확인하지 못함                                                                          |
| 내 가격                        | 계산하지 않음                                                                          |

확인되지 않은 가격·조건·기간을 채우거나 기존 keyless 결과로 대체하지 않았습니다. 이전 `everland-official` 실행의 5개 후보는 이번 OpenAI live 실행 결과가 아닙니다.

## 반영한 변경

- 기존 키를 보존하고 `SEARCH_PROVIDER=openai`로 전환했습니다.
- OpenAI SDK 자체 로깅을 `off`로 설정했습니다.
- 요청별 audit에는 단계, 모델, HTTP 상태, 허용된 오류 코드/종류, 공개 출처 URL, 지연만 남깁니다. 헤더·키·오류 원문·요청 본문은 기록하지 않습니다.
- `npm run verify:live`는 반드시 OpenAI 모드로 실제 엔진을 실행합니다. 설정된 secret 값은 출력·저장 직전 추가로 마스킹합니다.
- 사용 한도/결제 관련 실패는 `/api/search`에서 안전한 `OPENAI_QUOTA_EXCEEDED` 응답으로 안내하며 조용히 다른 검색 모드로 전환하지 않습니다.

## 재검증

OpenAI 프로젝트의 크레딧, 결제 상태, 사용 한도, 해당 키의 프로젝트 연결 상태를 확인한 뒤 다음 명령으로 재검증할 수 있습니다. 키 값을 대화나 로그에 공유할 필요가 없습니다.

```powershell
npm.cmd run verify:live
```

보고서는 `.scratch/live-report.json`에 저장됩니다. 성공하면 응답 후보별 eligibility·정가·가격과 실제 방문한 공식 URL을 이 보고서에서 확인할 수 있습니다. API 사용 한도의 정확한 계정 설정이나 잔액은 이 환경에서 조회하지 않았으며 추정하지 않습니다.
