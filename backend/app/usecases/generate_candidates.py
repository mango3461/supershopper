from app.api.schemas.common import (
    CandidateGenerationPayload,
    CandidateSeedPayload,
    ExpertSignalsPayload,
    IntentAnalysisPayload,
)
from app.domain.constants import MECHANICAL_KEYBOARD_REFERENCE_CANDIDATES
from app.ports.logger_port import LoggerPort


class GenerateCandidatesUseCase:
    def __init__(self, logger: LoggerPort) -> None:
        self._logger = logger

    def execute(
        self,
        intent: IntentAnalysisPayload,
        expert_signals: ExpertSignalsPayload,
        max_candidates: int,
    ) -> CandidateGenerationPayload:
        scored_candidates: list[CandidateSeedPayload] = []
        signal_texts = [
            f"{signal.title} {signal.snippet}".lower()
            for signal in expert_signals.signals
        ]

        for reference in MECHANICAL_KEYBOARD_REFERENCE_CANDIDATES:
            score = 0.0
            matched_signals = []

            for signal in expert_signals.signals:
                signal_text = f"{signal.title} {signal.snippet}".lower()
                if any(alias in signal_text for alias in reference["aliases"]):
                    score += 0.45
                    matched_signals.append(signal)
                elif reference["brand"].lower() in signal_text:
                    score += 0.18
                    matched_signals.append(signal)

            if not expert_signals.signals:
                score += 0.20

            if intent.preferred_noise_level == "quiet":
                if reference["noise_level"] == "quiet":
                    score += 0.20
                else:
                    score -= 0.25

            if reference["beginner_friendly"]:
                score += 0.15

            if intent.budget.max_price is not None:
                if reference["reference_price"] <= intent.budget.max_price:
                    score += 0.15
                elif reference["reference_price"] <= int(intent.budget.max_price * 1.05):
                    score += 0.04
                else:
                    score -= 0.20

            if intent.preferred_layout != "undecided" and intent.preferred_layout == reference["layout"]:
                score += 0.10
            elif intent.preferred_layout == "undecided" and reference["layout"] in {"75%", "TKL"}:
                score += 0.05

            preferred_key_feel = intent.preferred_key_feel
            switch_type = reference["switch_type"]
            if preferred_key_feel == "silent_linear_or_tactile":
                if switch_type in {"silent_linear", "silent_tactile"}:
                    score += 0.10
            elif preferred_key_feel and preferred_key_feel == switch_type:
                score += 0.10

            source_signal_titles = list(dict.fromkeys(signal.title for signal in matched_signals))
            if not source_signal_titles and any(alias in " ".join(signal_texts) for alias in reference["aliases"]):
                source_signal_titles.append("expert signal mention")

            source_signal_mode = self._infer_source_signal_mode(matched_signals)
            candidate_source_reason = self._build_candidate_source_reason(
                reference_name=reference["name"],
                matched_signals=matched_signals,
                source_signal_titles=source_signal_titles,
                source_signal_mode=source_signal_mode,
            )

            generation_reason = self._build_generation_reason(
                reference_name=reference["name"],
                rationale_signals=source_signal_titles,
                quiet_match=reference["noise_level"] == "quiet",
                budget_match=(
                    intent.budget.max_price is None
                    or reference["reference_price"] <= intent.budget.max_price
                ),
            )

            scored_candidates.append(
                CandidateSeedPayload(
                    candidate_id=reference["candidate_id"],
                    name=reference["name"],
                    brand=reference["brand"],
                    reference_price=reference["reference_price"],
                    inferred_layout=reference["layout"],
                    inferred_switch_type=reference["switch_type"],
                    inferred_noise_level=reference["noise_level"],
                    beginner_friendly=reference["beginner_friendly"],
                    rationale_signals=source_signal_titles[:3],
                    source_signal_titles=source_signal_titles[:3],
                    source_signal_mode=source_signal_mode,
                    generation_reason=generation_reason,
                    candidate_source_reason=candidate_source_reason,
                    heuristic_score=round(score, 3),
                )
            )

        ranked_candidates = sorted(
            scored_candidates,
            key=lambda item: (item.heuristic_score, item.reference_price is not None, -(item.reference_price or 0.0)),
            reverse=True,
        )

        minimum_target = max(3, min(max_candidates + 1, 4))
        shortlisted = [item for item in ranked_candidates if item.heuristic_score > 0][:minimum_target]
        if len(shortlisted) < minimum_target:
            fallback_candidates = [
                item for item in ranked_candidates if item.candidate_id not in {candidate.candidate_id for candidate in shortlisted}
            ]
            shortlisted.extend(fallback_candidates[: minimum_target - len(shortlisted)])

        payload = CandidateGenerationPayload(
            strategy=expert_signals.strategy,
            expert_signals=expert_signals.signals,
            candidates=shortlisted,
        )
        self._logger.debug(f"Generated {len(payload.candidates)} candidate seeds")
        return payload

    @staticmethod
    def _build_generation_reason(
        reference_name: str,
        rationale_signals: list[str],
        quiet_match: bool,
        budget_match: bool,
    ) -> str:
        reasons: list[str] = []
        if rationale_signals:
            reasons.append(f"{reference_name} 관련 expert signal이 감지되었습니다.")
        if quiet_match:
            reasons.append("저소음 조건과 잘 맞습니다.")
        if budget_match:
            reasons.append("예산 조건에 들어올 가능성이 높습니다.")
        return " ".join(reasons) if reasons else "입문용 기계식 키보드 기본 후보로 유지했습니다."

    @staticmethod
    def _infer_source_signal_mode(matched_signals) -> str:
        if not matched_signals:
            return "heuristic_only"
        has_live = any(signal.retrieval_source == "serpapi_live" for signal in matched_signals)
        has_fallback = any(signal.retrieval_source.startswith("mock") for signal in matched_signals)
        if has_live and has_fallback:
            return "mixed"
        if has_live:
            return "live"
        if has_fallback:
            return "fallback"
        return "unknown"

    @staticmethod
    def _build_candidate_source_reason(
        reference_name: str,
        matched_signals,
        source_signal_titles: list[str],
        source_signal_mode: str,
    ) -> str:
        if matched_signals:
            signal_list = ", ".join(source_signal_titles[:2])
            if source_signal_mode == "live":
                return f"{reference_name} 후보는 live expert signal에서 직접 언급된 콘텐츠를 근거로 생성했습니다: {signal_list}."
            if source_signal_mode == "fallback":
                return f"{reference_name} 후보는 fallback expert signal 콘텐츠를 근거로 생성했습니다: {signal_list}."
            if source_signal_mode == "mixed":
                return f"{reference_name} 후보는 live/fallback expert signal을 함께 참고해 생성했습니다: {signal_list}."
            return f"{reference_name} 후보는 expert signal 언급을 근거로 생성했습니다: {signal_list}."
        return f"{reference_name} 후보는 expert signal 직접 언급이 부족해 카테고리 기본 heuristic으로 유지했습니다."
