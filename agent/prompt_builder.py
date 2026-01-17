# -----------------------------
# ACTION PROMPT (IT SERVICE DESK)
# -----------------------------
def build_action_prompt(user_input: str) -> str:
    return f"""
You are an IT Service Desk automation engine.

Extract structured information from the user request.

FIELDS:
- department: IT / HR / Finance / Unknown
- issue_summary: short, professional description
- priority: Low / Medium / High

RULES:
- VPN, login, laptop, network, system access → IT
- Work-blocking issues → High priority
- Infer conservatively
- Return ONLY valid JSON
- No explanations

USER REQUEST:
"{user_input}"
"""


# -----------------------------
# INFORMATION PROMPT (RAG)
# -----------------------------
def build_prompt(question, section_text, tables, page):
    prompt = f"""
You are an enterprise document assistant.

TASK:
Answer strictly from the evidence provided.
Do NOT infer.
Do NOT calculate.

If the answer is NOT explicitly present, respond exactly with:
"Information not found in the document."

QUESTION:
{question}

EVIDENCE:
TEXT:
{section_text}
"""

    if tables:
        prompt += "\nTABLE DATA (AUTHORITATIVE):\n"
        for i, table in enumerate(tables, 1):
            prompt += f"\nTable {i}:\n{table}\n"

    prompt += """
OUTPUT RULES:
- If found:
  - Answer in 1–2 sentences
  - Quote values exactly
  - End with the page number explicitly shown in the text, e.g.:
    (Source: Page 107)
"""

    return prompt.strip()
