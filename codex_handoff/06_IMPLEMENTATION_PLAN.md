# Implementation Plan

## Suggested stack

-   Next.js
-   TypeScript
-   Tailwind CSS
-   OpenAI SDK / Responses API
-   Zod
-   Initially no DB
-   Later: Postgres/Supabase if needed

Do not hard-wire the entire app to one search provider. Define a search
abstraction so the implementation can later move from built-in web
search to an external search API if necessary.

## Suggested tree

``` text
app/
├── page.tsx
├── profile/page.tsx
├── search/page.tsx
└── api/
    └── search/route.ts

components/
├── common/
│   ├── Header.tsx
│   ├── Modal.tsx
│   └── Drawer.tsx
├── search/
│   ├── SearchBar.tsx
│   ├── SearchProgress.tsx
│   ├── BestPriceCard.tsx
│   └── BenefitResultCard.tsx
└── profile/
    ├── ProfileSidebar.tsx
    ├── BenefitChip.tsx
    └── BenefitSelector.tsx

lib/
├── ai/
│   ├── client.ts
│   ├── parseIntent.ts
│   ├── planSearch.ts
│   ├── searchBenefit.ts
│   └── resolveBasePrice.ts
├── benefits/
│   ├── eligibility.ts
│   ├── calculate.ts
│   ├── deduplicate.ts
│   └── rank.ts
├── search/
│   ├── provider.ts
│   └── types.ts
└── profile/
    └── mockProfile.ts

schemas/
├── profile.ts
├── intent.ts
├── searchPlan.ts
├── benefit.ts
└── response.ts

prompts/
├── queryParser.ts
├── searchPlanner.ts
├── benefitExtractor.ts
└── basePriceResolver.ts
```

## Phase 1 --- Engine PoC

Goal: no polished UI.

Implement: 1. schemas 2. mock profile 3. parseIntent 4. planSearch 5.
searchBenefit 6. resolveBasePrice 7. eligibility 8. calculate 9.
deduplicate/rank

Test query: `에버랜드`

Output structured JSON and readable terminal logs.

Do not proceed to heavy UI work until at least one real query produces
evidence-backed results.

## Phase 2 --- API

`POST /api/search`

Request:

``` json
{
  "query": "에버랜드"
}
```

Response should conform to SearchResponse.

For MVP, synchronous request is acceptable if latency is tolerable. If
not, introduce job id + SSE only after measuring.

## Phase 3 --- UI

1.  Home search
2.  Search loading
3.  Search result
4.  Profile sidebar
5.  Profile page
6.  Benefit detail drawer
7.  responsive mobile behavior

## Phase 4 --- Reliability

-   timeouts
-   per-task error isolation
-   source validation
-   expiration filtering
-   malformed model output handling
-   duplicate merging
-   missing base price state
-   no-benefit state

## Engineering rules

-   No fake data in production search result path.
-   Demo fixtures are allowed only behind explicit mock/dev flag.
-   Do not silently replace failed web search with invented sample data.
-   Keep model names/config in environment/config.
-   Keep prompts centralized.
-   Validate all model output.
-   Parallelize independent searches with a safe concurrency limit.
-   One failed search task must not fail the whole request.
-   Log task category, latency, source count, extraction status; never
    log secrets.
