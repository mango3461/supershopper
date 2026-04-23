INTENT_PROMPT = """Analyze the shopping intent for the mechanical keyboard recommendation flow.
Return structured data for:
- category
- user_level
- budget
- constraints
- prioritized_attributes
- preferred_noise_level
- preferred_key_feel
- preferred_layout
- interpretation_summary
User query: {query}
"""


def render(query: str) -> str:
    return INTENT_PROMPT.format(query=query)
