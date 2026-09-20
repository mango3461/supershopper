# Acceptance Criteria

## Engine

-   [ ] `에버랜드` can be parsed into PurchaseIntent.
-   [ ] Search plan includes relevant personal and discovery tasks.
-   [ ] Independent search tasks run concurrently or with controlled
    concurrency.
-   [ ] Every surfaced confirmed benefit has a source.
-   [ ] Expired promotion is not shown as current.
-   [ ] Unsupported discount values are not invented.
-   [ ] Benefit extraction validates against schema.
-   [ ] eligibility can return confirmed / needs_info / not_eligible.
-   [ ] price arithmetic is performed in code.
-   [ ] duplicate benefits are merged.
-   [ ] official sources are preferred.

## Result integrity

-   [ ] `best` contains only a benefit eligible for the current user.
-   [ ] Discovery opportunities requiring something the user does not
    own are separated from `best`.
-   [ ] If base price cannot be established, UI does not fabricate
    `내 가격`.
-   [ ] Missing profile information is surfaced explicitly.
-   [ ] Source URL/title and checked/retrieved time are available.

## UI

-   [ ] PC web works.
-   [ ] Mobile responsive works.
-   [ ] Home is search-first, not chat-first.
-   [ ] Search result emphasizes `내 가격`.
-   [ ] Desktop result has result + profile sidebar.
-   [ ] Mobile profile/detail uses drawer/bottom sheet.
-   [ ] Loading state communicates which benefit categories are being
    checked.
-   [ ] `confirmed`, `needs_info`, `not_eligible` are visually
    distinguishable.
-   [ ] Official source can be opened from benefit detail.

## Failure states

-   [ ] no result
-   [ ] web search partial failure
-   [ ] LLM malformed output
-   [ ] base price unknown
-   [ ] benefit found but conditions unknown
-   [ ] source conflict
-   [ ] timeout

## MVP success

A reviewer can: 1. open the web app on a PC, 2. search `에버랜드`, 3.
see the service explore multiple benefit dimensions, 4. see
evidence-backed applicable discounts, 5. understand which ones are
applicable/uncertain, 6. see an estimated personal price when enough
evidence exists, 7. inspect the official source, 8. resize/use mobile
and retain the same core flow.
