# Codex Master Prompt

You are implementing a hackathon MVP called **슈퍼쇼퍼 (Super Shopper)**.

Before writing code, read every markdown file in this handoff directory,
especially: - 00_README.md - 01_PRODUCT_SPEC.md - 02_UX_SPEC.md -
03_ARCHITECTURE.md - 04_DATA_SCHEMAS.md - 05_LLM_PROMPTS.md -
06_IMPLEMENTATION_PLAN.md - 07_ACCEPTANCE_CRITERIA.md

Treat those files as the product and engineering specification.

## Objective

Build a responsive PC/mobile web application where a user can register
benefit-related profile information (cards, mobile carrier, memberships,
age/status/location), search a merchant or purchase target such as
`에버랜드`, and receive evidence-backed current discounts discovered
from the web.

The product's primary output is not an AI answer. It is:

-   the user's estimated personal price (`내 가격`) when it can be
    safely calculated,
-   the best currently applicable discount,
-   alternatives,
-   missing information required to verify uncertain benefits,
-   official evidence/source links.

The UI must feel like a personalized price-search product, not a
chatbot.

## Critical architecture rule

Do NOT implement this as one prompt: `profile + query -> answer`.

Use the staged architecture in the docs:

query parsing → search planning → parallel web/evidence search → benefit
normalization → eligibility evaluation → base price resolution →
deterministic price calculation → deduplication/ranking → UI.

Use LLMs for understanding/planning/extracting unstructured evidence.
Use deterministic TypeScript code for arithmetic and rule evaluation
whenever possible.

## Reliability requirements

Never fabricate: - discount existence - discount percentage - price -
eligibility requirement - valid period - stacking compatibility - source

Unknown information must remain unknown.

A benefit cannot be displayed as confirmed without evidence. Expired
promotions cannot be displayed as current. If the base price is
uncertain, do not fabricate a final personal price.

Prefer official merchant/provider sources.

## Development strategy

Do not start by polishing every screen.

First make the end-to-end engine work for:

QUERY: `에버랜드`

MOCK PROFILE: - age: 26 - location: 서울 - occupation: 대학생 - carrier:
SKT - carrier grade: unknown - card: 현대카드 ZERO Edition3 -
membership: 네이버플러스

Build and validate the engine first. Once the engine can return
schema-valid, evidence-backed results, connect it to the UI.

## Stack

Prefer: - Next.js - TypeScript - Tailwind CSS - Zod - OpenAI Responses
API / web search where supported

Keep the web-search implementation behind an abstraction so it can later
be replaced or supplemented by another provider.

Initially avoid unnecessary infrastructure: - no authentication unless
required - no database unless required - use mock profile initially - do
not add queues/SSE until latency measurements justify them

## Implementation behavior

1.  Inspect the existing repository first.
2.  Preserve useful existing structure/configuration.
3.  Create a short implementation plan.
4.  Implement Phase 1 engine.
5.  Run typecheck/lint/tests.
6.  Fix errors before continuing.
7.  Implement API.
8.  Implement desktop UI.
9.  Add responsive mobile behavior.
10. Test failure/unknown states.
11. Update README with setup instructions and required environment
    variables.
12. Summarize what was implemented and any remaining limitations.

Do not merely generate a scaffold and stop. Implement a working vertical
slice.

If an API/library detail may have changed, verify current official
documentation rather than guessing.

## Definition of done

Use `07_ACCEPTANCE_CRITERIA.md` as the checklist.

The most important demo flow is:

Home → search `에버랜드` → visible multi-source exploration →
applicable/uncertain discounts → `내 가격` if safely calculable →
benefit detail → official source.

Prioritize correctness and traceability over the number of discounts
returned.
