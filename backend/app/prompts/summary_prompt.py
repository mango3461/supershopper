from app.api.schemas.common import EvidenceFilteringPayload, IntentAnalysisPayload


SUMMARY_PROMPT = """Summarize retrieved shopping evidence for the user.
Category: {category}
User level: {user_level}
Candidate count: {candidate_count}
Preferred noise: {noise}
Return:
- summary
- comparison_points
- beginner_tip
- tradeoff_note
"""


def render(intent: IntentAnalysisPayload, filtered: EvidenceFilteringPayload) -> str:
    return SUMMARY_PROMPT.format(
        category=intent.category,
        user_level=intent.user_level,
        candidate_count=len(filtered.products),
        noise=intent.preferred_noise_level,
    )
