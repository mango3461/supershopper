# 슈퍼쇼퍼 (Super Shopper) --- Codex Handoff

이 폴더는 해커톤 MVP를 Codex가 구현할 때 참고할 제품/기술 명세다.

## 목표

사용자가 자신이 보유한 카드·통신사·멤버십·개인 조건을 등록하고,
결제하려는 장소/상품을 검색하면 현재 웹의 할인 정보를 탐색해 **"내가
지금 실제로 결제할 수 있는 가장 낮은 가격"**을 보여주는 반응형 웹을
만든다.

핵심 문장: \> 정가는 같아도, 내 가격은 다르니까.

사용자 입력은 가능한 한 짧아야 한다. 예: `에버랜드`

서비스가 사용자의 프로필을 바탕으로 카드, 통신사, 멤버십,
연령/신분/지역, 판매처 프로모션 등을 탐색한다.

## 가장 중요한 개발 원칙

1.  AI 챗봇 UI로 만들지 않는다. 검색 서비스처럼 보이게 한다.
2.  LLM은 이해·탐색 계획·비정형 정보 구조화에 사용한다.
3.  가격 계산, eligibility의 명확한 규칙, 정렬은 코드로 처리한다.
4.  할인율/조건/기간을 추측하지 않는다.
5.  공식 출처를 우선한다.
6.  확인되지 않은 정보는 `needs_info` 또는 `unknown`으로 표현한다.
7.  혜택 DB를 직접 구축하는 것이 MVP 목표가 아니다. 최신 정보는 웹에서
    탐색한다.
8.  DB가 필요하다면 사용자 Profile / Search History / Savings History
    중심이다.
9.  PC와 모바일 모두 지원하는 반응형 웹이어야 한다.
10. 먼저 end-to-end PoC를 성공시킨 뒤 UI를 확장한다.

## 권장 구현 순서

1.  고정 프로필 + `에버랜드`로 terminal/API PoC
2.  웹 탐색 → BenefitCandidate JSON
3.  eligibility
4.  base price + 가격 계산
5.  deduplicate/rank
6.  `/api/search`
7.  PC 검색 결과 UI
8.  Profile UI
9.  모바일 반응형
10. 필요 시 DB/로그인/절약 기록

## 문서

-   `01_PRODUCT_SPEC.md`: 문제, 사용자 가치, MVP 범위
-   `02_UX_SPEC.md`: PC/모바일 화면 및 상태
-   `03_ARCHITECTURE.md`: 전체 파이프라인과 책임 분리
-   `04_DATA_SCHEMAS.md`: TypeScript/Zod 데이터 모델
-   `05_LLM_PROMPTS.md`: LLM 역할별 프롬프트
-   `06_IMPLEMENTATION_PLAN.md`: 파일 구조와 구현 순서
-   `07_ACCEPTANCE_CRITERIA.md`: 완료 판정 기준
-   `CODEX_MASTER_PROMPT.md`: Codex에 그대로 넣을 메인 프롬프트
