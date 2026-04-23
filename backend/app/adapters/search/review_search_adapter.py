from app.api.schemas.common import ProductPayload, ReviewSnippet, SearchStrategyPayload


MOCK_REVIEW_LIBRARY = {
    "keyboard-1": [
        ReviewSnippet(
            source="keyboard-community",
            snippet="75% 배열이 작지만 화살표 키를 유지해서 실사용이 편하다는 평가가 많습니다.",
            rating=4.6,
            url="https://example.com/reviews/keymellow-75-flex/community",
        ),
        ReviewSnippet(
            source="editorial-review",
            snippet="저소음 택타일 스위치가 사무실에서도 쓸 만할 정도로 조용하면서도 눌림 감각은 남는다는 평가가 있습니다.",
            rating=4.5,
            url="https://example.com/reviews/keymellow-75-flex/editorial",
        ),
    ],
    "keyboard-2": [
        ReviewSnippet(
            source="keyboard-community",
            snippet="저소음 적축 옵션이 가장 조용하고 오래 써도 부담이 적다는 의견이 꾸준합니다.",
            rating=4.4,
            url="https://example.com/reviews/lumakeys-flow-tkl/community",
        ),
        ReviewSnippet(
            source="video-review",
            snippet="처음 커스텀 스타일 키보드를 사는 사람도 텐키리스 형태는 적응이 빠르다는 평가가 많습니다.",
            rating=4.3,
            url="https://example.com/reviews/lumakeys-flow-tkl/video",
        ),
    ],
    "keyboard-3": [
        ReviewSnippet(
            source="office-user-review",
            snippet="사무실에서 쓰기엔 충분히 조용하지만, 풀배열이라 생각보다 자리 차지가 크다는 후기가 있습니다.",
            rating=4.2,
            url="https://example.com/reviews/monotype-office-98/users",
        ),
        ReviewSnippet(
            source="editorial-review",
            snippet="처음부터 숫자패드가 꼭 필요하다면 비교적 안전한 풀배열 선택지라는 평가입니다.",
            rating=4.1,
            url="https://example.com/reviews/monotype-office-98/editorial",
        ),
    ],
    "keyboard-4": [
        ReviewSnippet(
            source="keyboard-community",
            snippet="재미있는 클릭감은 있지만 거의 모든 리뷰가 소음이 크다고 경고합니다.",
            rating=3.8,
            url="https://example.com/reviews/clickforge-rgb-pro/community",
        ),
    ],
    "keyboard-5": [
        ReviewSnippet(
            source="editorial-review",
            snippet="기본 타건음 완성도는 좋지만 가격이 입문 예산을 자주 넘어간다는 의견이 있습니다.",
            rating=4.7,
            url="https://example.com/reviews/atelier-loop-75/editorial",
        ),
        ReviewSnippet(
            source="keyboard-community",
            snippet="큰 튜닝 없이도 완성도 높은 75% 배열을 원하는 사용자에게 인기가 있습니다.",
            rating=4.8,
            url="https://example.com/reviews/atelier-loop-75/community",
        ),
    ],
}


class ReviewSearchAdapter:
    def search_reviews(
        self, products: list[ProductPayload], strategy: SearchStrategyPayload
    ) -> list[ProductPayload]:
        del strategy
        enriched_products: list[ProductPayload] = []
        for product in products:
            review_snippets = MOCK_REVIEW_LIBRARY.get(product.product_id, [])
            enriched_products.append(
                product.model_copy(update={"evidence": review_snippets})
            )
        return enriched_products
