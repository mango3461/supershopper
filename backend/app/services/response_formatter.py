from app.api.schemas.common import RecommendationPayload


class ResponseFormatter:
    def format_chat_reply(self, recommendation: RecommendationPayload) -> str:
        if recommendation.recommended_choice is None:
            return "아직 조건에 맞는 추천 후보를 충분히 만들지 못했습니다. 예산이나 조건을 조금 더 알려주면 정확도가 올라갑니다."

        top_pick = recommendation.recommended_choice
        return (
            f"우선 추천은 {top_pick.name}입니다. "
            f"{recommendation.buying_guide_summary.summary} "
            f"추천 이유는 {recommendation.recommendation_reason}"
        )
