# 슈퍼쇼퍼 · SuperShopper

정가는 같아도, 내 가격은 다르니까. 보유한 카드·통신사·멤버십·개인 조건으로 공식 할인 근거를 찾는 반응형 가격 검색 MVP입니다. 구현 기준은 `codex_handoff/CODEX_MASTER_PROMPT.md`와 동봉된 문서 8개입니다.

## 실행

Node.js 22 이상을 권장합니다. Windows PowerShell 실행 정책이 `npm.ps1`을 막으면 아래처럼 `npm.cmd`를 사용하세요. macOS/Linux에서는 `npm`으로 바꾸면 됩니다.

```powershell
npm.cmd ci
npm.cmd run dev
```

<http://localhost:3000>에서 사용합니다. 키 없이도 **실시간 에버랜드 공식 페이지**를 읽습니다. 검색 결과에 고정 샘플이나 저장된 PoC 결과를 섞지 않습니다.

```powershell
npm.cmd run poc
npm.cmd run typecheck
npm.cmd run lint
npm.cmd test
npm.cmd run build
npm.cmd run start
```

`poc`는 실제 `에버랜드` 쿼리를 실행하고 JSON을 출력하며 `.scratch/poc-result.json`에 저장합니다. 이 파일은 런타임 검색에 사용하지 않습니다.

## 두 검색 모드

| 모드                  | 설정                                         | 실제 동작 / 범위                                                                                                                    |
| --------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 공식 페이지 직접 탐색 | `SEARCH_PROVIDER=everland`                   | 키 불필요. 에버랜드 공식 목록에서 상세 URL을 발견하고 본문을 새로 가져옵니다. 카드·대학(원)생·공개 프로모션 일부 경로만 지원합니다. |
| LLM 웹 검색           | `SEARCH_PROVIDER=openai` 및 `OPENAI_API_KEY` | 자연어 이해 → 검색 계획 → Responses 웹 검색 → 공식 본문 재조회 → Structured Outputs 추출 → 코드 검증.                               |
| Gemini 웹 검색        | `SEARCH_PROVIDER=gemini` 및 `GEMINI_API_KEY` | 자연어 이해 → 검색 계획 → Gemini `googleSearch` grounding → citation 최종 URL 재조회 → JSON/Zod 추출 → 동일한 코드 검증. |

키와 provider를 모두 생략하면 직접 탐색 모드입니다. provider를 생략하고 키만 설정하면 OpenAI 모드입니다. `openai` 또는 `gemini` 실패 시 다른 모드나 샘플로 조용히 전환하지 않습니다.

```powershell
Copy-Item .env.example .env.local
```

`.env.local`에서 다음을 설정한 뒤 서버를 재시작하세요. API 키를 브라우저 코드나 `NEXT_PUBLIC_*` 환경변수에 넣지 마세요.

```dotenv
SEARCH_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5-mini
SEARCH_CONCURRENCY=3
```

모델은 환경변수로 교체합니다. 계정에서 Responses, web search, Structured Outputs를 지원하는 모델 접근 권한이 필요합니다. `.env.local`은 git ignore 대상입니다. LLM 모드에는 API 사용료가 발생합니다.

## 검증된 데모 흐름

1. 홈에서 `에버랜드` 검색. 초기 프로필은 문서의 26세·서울·대학생·SKT·현대카드 ZERO Edition3·네이버플러스입니다.
2. 카드, 신분, 공개 프로모션의 실제 공식 페이지를 확인합니다. 결과의 탐색 기록에서 완료·미지원·실패를 구분합니다. 로딩 표시는 진행률을 임의로 완성하지 않습니다.
3. 내 프로필 경로와 공개 혜택을 별도로 봅니다. 각 후보의 적용 상태와 확인할 조건이 표시됩니다.
4. `조건 자세히 보기`에서 증빙·실적·기간·본문 인용·확인 시점을 확인하고 공식 페이지를 엽니다.
5. 프로필을 수정·저장하고 다시 검색합니다. 방문일도 선택할 수 있습니다.
6. 모바일에서는 `내 혜택 보기`와 혜택 상세가 바텀시트로 열립니다.

**2026-09-20 실제 검증에서는 공식 후보 5개를 찾았고 전부 `needs_info`였습니다. `confirmed`나 최종 가격을 확인했다는 뜻이 아닙니다.** 직접 탐색 모드는 이미지 속 전체 기간과 동적 날짜별 정가를 읽지 못하므로 `best=null`, `basePrice=null`, `finalPrice=null`을 유지합니다. 날짜를 입력해도 공식 가격을 읽지 못하면 가격은 표시하지 않습니다.

가격이 충분히 검증된 경로의 계산은 구현되어 있습니다. LLM 모드에서는 예를 들어 `2026-09-25 에버랜드 종일권 대인 1명`처럼 구체적으로 입력할 수 있습니다. 단, 실제 출처가 날짜·상품·연령 구분·채널·인원을 뒷받침하고 eligibility까지 확인된 경우에만 예상 결제가가 생깁니다. 이 쿼리로 가격이 반드시 나온다고 보장하지 않습니다.

## 구조

```text
schemas/                   Zod: 입력, 프로필, 의도, 계획, 혜택, 정가, 응답
prompts/                   LLM 역할별 프롬프트
lib/ai/                    Responses SDK + Structured Outputs + 웹 검색 어댑터
lib/search/provider.ts     교체 가능한 SearchProvider 인터페이스
lib/search/everland.ts     실제 공식 HTML 기반 제한 어댑터
lib/search/evidence.ts     공식 호스트 검증, 제한된 본문 fetch
lib/search/engine.ts       전체 파이프라인, 동시성, 실패 격리, 로그
lib/benefits/              eligibility / 계산 / 중복·충돌 / 정렬
app/api/search/route.ts    POST /api/search
app/                      홈 / 검색 / 프로필
components/               반응형 결과·상세·프로필
tests/                    네트워크 없는 엔진 회귀 테스트 (합성 입력)
e2e/                      실제 공식 검색 + 브라우저 / API 테스트
docs/ACCEPTANCE.md         인수 기준별 증거와 미완료 사항
```

### API

```http
POST /api/search
Content-Type: application/json

{"query":"에버랜드"}
```

선택적으로 `profile`과 ISO 형식의 `visitDate`를 받습니다. `schemas/index.ts`가 계약의 source of truth입니다. 응답은 명세의 `best`, `alternatives`, `opportunities`에 `intent`, `tasks`, `warnings`, `provider`, `checkedAt`, `basePriceReason`, `elapsedMs`를 추가합니다.

400 입력 오류, 413 본문 제한 초과, 415 잘못된 형식, 422 제한 모드 미지원 쿼리, 429 동시 요청 초과, 502 추출/연결 실패, 503 설정 누락, 504 시간 초과를 구분합니다. 개별 탐색 실패는 가능한 나머지 결과와 경고로 반환합니다.

### 정확성 제약

- 모든 모델 구조화 출력은 Zod로 검증합니다. 웹 검색의 자연어 답변은 결과로 소비하지 않고, 검증된 citation URL의 실제 본문을 다시 읽습니다.
- 알려진 공식 HTTPS 도메인만 서버에서 fetch합니다. 임의 URL, 비표준 포트, 사용자 정보 URL, 자동 리다이렉트를 차단합니다. 네이버 사용자 블로그는 공식 출처로 취급하지 않습니다.
- 인용문이 원문에 있는지, 추출 수치·기간이 인용문에 있는지 추가 검사합니다. 수치·기간 검증 실패는 금액을 지우고 `unknown`으로 낮춥니다.
- 명확한 불일치는 `not_eligible`, 부족한 프로필 정보는 `needs_info`, 부족한 출처/불완전 조건은 `unknown`, 모든 필수 조건이 확인된 경우에만 `confirmed`입니다. 프로필 값 자체는 사용자 신고 정보입니다.
- 가격은 TypeScript로 계산합니다. 정가, 문맥, 적용 여부, 계산 안전성 확인 없이 계산하지 않습니다. 할인율, 정액, 특가와 할인 한도를 지원합니다. 소수 원 반올림을 추측하지 않으며, 포인트 차감·캐시백·동반자 일괄 계산·중복 할인 최적화는 제외합니다.
- 완전히 일치하는 구매 문맥의 1인 가격만 계산합니다. 그룹 전체에 개인 할인을 곱하지 않습니다.
- 종료된 기간은 현재 혜택에서 제외합니다. 출처의 수치·기간 충돌은 계산하지 않습니다. `best`는 적용 확인과 가격 계산을 모두 통과해야 합니다.
- 최대 8개 검색 계획, 1~4개 동시 작업, 페이지당 12초/2MB, OpenAI 호출 45초, 전체 요청 150초 제한이 있습니다. 프로세스당 3개 검색 요청만 동시 처리합니다.
- 로그에는 category·latency·source count·상태만 남깁니다. API 키나 프로필/검색 원문은 로깅하지 않습니다. DB나 로그인은 없습니다.

프로필은 브라우저 localStorage에만 영구 저장합니다. 검색 시 서버로 전달되며, OpenAI 모드에서는 의도 분석/계획/정가 확인을 위해 OpenAI로 전달됩니다. Responses `store:false`를 사용합니다. 이 설정을 외부 제공자의 전체 데이터 보관 정책에 대한 보장으로 해석하면 안 됩니다.

## 브라우저 테스트

```powershell
npm.cmd run build
npm.cmd run test:e2e
```

Windows에 Edge가 있으면 headless Edge를 사용합니다. 그렇지 않으면 먼저 `npx playwright install chromium`을 실행하세요. `PLAYWRIGHT_CHANNEL`로 채널을 선택할 수도 있습니다. E2E 실행 시 `SEARCH_PROVIDER=everland`를 사용하고 별도 OpenAI 환경 설정 없이 실행하세요. 실시간 출처가 바뀌거나 접속이 차단되면 라이브 테스트는 실패할 수 있습니다.

스크린샷은 `.scratch/desktop-home.png`, `desktop-results.png`, `mobile-home.png`, `mobile-results.png`, `mobile-detail.png`에 생성됩니다. 실패 trace는 `test-results/`에 있습니다.

## 현재 한계와 다음 순서

1. **OpenAI live 실호출**: 키를 연결하고 `SEARCH_PROVIDER=openai`로 전환했습니다. 실제 Responses 요청은 첫 의도 분석에서 사용 한도/결제 관련 HTTP 429로 거절되었습니다. 웹 검색·추출의 성공 검증은 아직 남아 있습니다. [실행 보고서](docs/LIVE_VERIFICATION.md)를 확인하세요. 한도 문제 해결 후 `npm.cmd run verify:live`로 재검증할 수 있습니다.
2. **공식 예약 가격/기간 수집 강화**: 이미지의 조건, 연간 날짜 문맥, 로그인·동적 예약 화면과 날짜 등급을 다룰 전용 검증기가 필요합니다. 지금은 안전하게 계산을 보류합니다.
3. **필드별 근거 강화**: 원문에 숫자가 있다는 사실만으로 숫자의 의미까지 증명되지는 않습니다. LLM의 조건 누락과 문맥 오인 가능성이 남습니다. 필드별 인용·교차 검증·고정 평가셋이 우선입니다.
4. **제공자 확대**: 공식 도메인 허용 목록과 content adapter를 추가해야 다른 판매처를 충분히 지원합니다. 서버 fetch가 리다이렉트/PDF/이미지를 지원하지 않으므로 일부 정상 출처도 누락됩니다.
5. **공개 서비스 운영**: 지금은 로컬/해커톤 MVP입니다. 외부 배포 전 사용자별 분산 rate limit·비용 한도·관측·접근 정책을 추가해야 합니다. 단일 프로세스 동시성 제한만 구현되어 있습니다.

## 확인한 공식 개발 문서

- [OpenAI Responses 웹 검색](https://developers.openai.com/api/docs/guides/tools-web-search)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Next.js 설치 및 App Router](https://nextjs.org/docs/app/getting-started/installation)
- [에버랜드 공식 스마트예약](https://reservation.everland.com/web/el.do?method=productMain)

SDK와 API 형태는 위 공식 문서를 확인하고 구현했습니다. 외부 문서의 기능 설명과 이 저장소에서 실제로 실행해 검증한 범위는 구분합니다.
