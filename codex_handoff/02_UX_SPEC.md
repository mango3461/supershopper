# UX Spec

## 공통 원칙

-   Chat UI 금지. 검색 엔진/가격 비교 서비스 형태.
-   결과에서 가장 크게 보여줄 정보는 `내 가격`.
-   AI의 긴 설명보다 구조화된 카드/테이블.
-   출처와 확인 상태를 명확하게 표시.
-   Desktop-first로 만들되 모바일까지 반응형 지원.

## 1. Home `/`

구성: - Header - Hero - SearchBar - 예시 검색 chip - My Benefit Preview

Hero: - `정가는 같아도, 내 가격은 다르니까.` -
`카드부터 통신사, 멤버십까지. 내가 받을 수 있는 할인을 한 번에 찾아보세요.`

Search: - placeholder: `어디에서 결제하시나요?` - 예: 에버랜드 / CGV /
KTX / 스타벅스

## 2. My Benefits `/profile`

사용자에게 "개인정보 입력"보다 "내 혜택 등록"으로 인식시킨다.

섹션: - 카드 - 통신사 - 멤버십 - 개인 조건(나이/생년, 학생 여부, 지역
등)

문구: \> 카드번호나 결제정보는 필요하지 않아요.

정확한 카드 상품명을 받을 수 있도록 검색/선택 UI를 둔다.

## 3. Search `/search?q=...`

### Loading

Desktop: - 상단 검색창 - 좌측: 탐색 진행 - 우측: ProfileSidebar

진행 예: - 현대카드 ✓ - SKT ● - 네이버플러스 ✓ - 대학생 ● - 연령 ○ -
지역 ○ - 현재 프로모션 ○

### Result

Desktop 레이아웃: - 좌측 약 70%: 결과 - 우측 약 30%: 내 혜택

BestPriceCard: - 대상명 - `내 가격` - 예상 결제가 - 정가 - 절약액 - BEST
혜택 - 할인받는 방법 CTA

Alternatives: - 제공자 - 할인 - 예상 결제가 - eligibility - source
status

## 4. Benefit Detail

Desktop: Right Drawer Mobile: Bottom Sheet

표시: - 할인명/제공자 - 할인율 또는 특가 - 예상 결제가 - 왜 해당되는지 -
추가 확인 정보 - 이용 조건 - 유효기간 - 구매 채널 - 공식 출처 - 확인
시점 - 공식 페이지 CTA

## 5. Responsive

Desktop: `[Result 70%][Profile 30%]`

Mobile: - Result full width - `내 혜택 N개` 버튼 - Profile은 Bottom
Sheet - Benefit detail도 Bottom Sheet

## 6. 상태 UI

-   확인됨: `confirmed`
-   추가 정보 필요: `needs_info`
-   해당 없음: `not_eligible`
-   근거 부족: `unknown`

LLM이 불확실한 것을 확정형 문구로 표현하지 않는다.
