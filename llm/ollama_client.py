import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"


def call_ollama(prompt: str, timeout: int = 180) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        # Return RAW model output only
        return response.json().get("response", "").strip()

    except Exception as e:
        # ❗ IMPORTANT:
        # Do NOT return semantic text here
        # Let supervisor decide refusal behavior
        print(f"⚠️ Ollama call failed: {e}")
        return ""
