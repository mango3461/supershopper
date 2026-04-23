from app.api.schemas.common import ProductPayload, SearchStrategyPayload


MECHANICAL_KEYBOARD_CATALOG = [
    ProductPayload(
        product_id="keyboard-1",
        name="KeyMellow 75 Flex",
        brand="KeyMellow",
        price=149000,
        url="https://example.com/products/keymellow-75-flex",
        layout="75%",
        switch_type="silent_tactile",
        noise_level="quiet",
        key_feel="light_tactile",
        connectivity=["wired", "2.4g", "bluetooth"],
        hot_swappable=True,
        beginner_friendly=True,
        strengths=[
            "화살표 키와 기능열을 유지하면서도 책상 공간을 덜 차지합니다.",
            "조용한 택타일 스위치라 피드백은 있으면서도 소음이 크지 않습니다.",
            "핫스왑 지원으로 나중에 스위치를 바꾸기 쉽습니다.",
        ],
        cautions=[
            "75% 배열이 익숙하지 않다면 며칠 정도 적응이 필요할 수 있습니다.",
        ],
        attributes={
            "case_mount": "gasket",
            "stabilizer": "factory_lubed",
            "backlight": "white",
        },
        relevance_score=0.82,
    ),
    ProductPayload(
        product_id="keyboard-2",
        name="LumaKeys Flow TKL",
        brand="LumaKeys",
        price=129000,
        url="https://example.com/products/lumakeys-flow-tkl",
        layout="TKL",
        switch_type="silent_linear",
        noise_level="quiet",
        key_feel="smooth_linear",
        connectivity=["wired"],
        hot_swappable=True,
        beginner_friendly=True,
        strengths=[
            "타건 소음이 낮아 공유 공간에서 쓰기 편합니다.",
            "텐키리스 배열이라 익숙한 형태를 유지하면서도 공간을 절약합니다.",
            "예산 여유가 남아 손목 받침대나 여분 스위치를 추가하기 좋습니다.",
        ],
        cautions=[
            "유선 연결만 지원합니다.",
        ],
        attributes={
            "case_mount": "tray",
            "stabilizer": "pre_tuned",
            "backlight": "rgb",
        },
        relevance_score=0.8,
    ),
    ProductPayload(
        product_id="keyboard-3",
        name="MonoType Office 98",
        brand="MonoType",
        price=139000,
        url="https://example.com/products/monotype-office-98",
        layout="full_size",
        switch_type="silent_tactile",
        noise_level="quiet",
        key_feel="soft_tactile",
        connectivity=["wired", "bluetooth"],
        hot_swappable=False,
        beginner_friendly=True,
        strengths=[
            "풀배열이라 처음 써도 이해하기 쉬운 편입니다.",
            "조용한 택타일 스위치라 사무실에서도 무난합니다.",
            "블루투스를 지원해 데스크 환경이 바뀌어도 대응하기 쉽습니다.",
        ],
        cautions=[
            "75%나 텐키리스보다 책상 공간을 더 차지합니다.",
        ],
        attributes={
            "case_mount": "top",
            "stabilizer": "factory_tuned",
            "backlight": "none",
        },
        relevance_score=0.74,
    ),
    ProductPayload(
        product_id="keyboard-4",
        name="ClickForge RGB Pro",
        brand="ClickForge",
        price=99000,
        url="https://example.com/products/clickforge-rgb-pro",
        layout="TKL",
        switch_type="clicky",
        noise_level="loud",
        key_feel="sharp_clicky",
        connectivity=["wired"],
        hot_swappable=False,
        beginner_friendly=False,
        strengths=[
            "클릭감이 분명해 확실한 타건 피드백을 원하는 사람에게는 장점이 될 수 있습니다.",
        ],
        cautions=[
            "클릭음이 뚜렷해서 소음이 크게 느껴질 수 있습니다.",
        ],
        attributes={
            "case_mount": "tray",
            "stabilizer": "basic",
            "backlight": "rgb",
        },
        relevance_score=0.52,
    ),
    ProductPayload(
        product_id="keyboard-5",
        name="Atelier Loop 75",
        brand="Atelier",
        price=169000,
        url="https://example.com/products/atelier-loop-75",
        layout="75%",
        switch_type="silent_linear",
        noise_level="quiet",
        key_feel="refined_linear",
        connectivity=["wired", "2.4g"],
        hot_swappable=True,
        beginner_friendly=True,
        strengths=[
            "타건음과 마감이 한 단계 더 고급스럽게 느껴집니다.",
            "기본 튜닝이 괜찮아 저소음 성향을 비교적 잘 살립니다.",
        ],
        cautions=[
            "이번 MVP 시나리오 기준 예산을 초과합니다.",
        ],
        attributes={
            "case_mount": "gasket",
            "stabilizer": "hand_lubed",
            "backlight": "south_facing_rgb",
        },
        relevance_score=0.84,
    ),
]


class ShoppingSearchAdapter:
    def search_products(self, strategy: SearchStrategyPayload) -> list[ProductPayload]:
        del strategy
        return [item.model_copy(deep=True) for item in MECHANICAL_KEYBOARD_CATALOG]
