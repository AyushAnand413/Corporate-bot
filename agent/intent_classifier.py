from llm.ollama_client import call_ollama

INTENT_PROMPT = """
You are an enterprise IT assistant.

Classify the user request into exactly ONE category:
- ACTION (creating a ticket, fixing an issue, requesting help)
- INFORMATION (asking a question)

User input:
"{query}"

Return ONLY the category name.
"""

def classify_intent(query: str) -> str:
    result = call_ollama(INTENT_PROMPT.format(query=query)).strip().upper()

    if result not in ("ACTION", "INFORMATION"):
        return "INFORMATION"

    return result
