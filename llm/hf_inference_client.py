import os
import time
from typing import Any

import requests


class HFGenerationError(Exception):
    pass


class HFInferenceClient:

    def __init__(
        self,
        api_token: str,
        generation_model: str,
        timeout: int = 180,          # ✅ increased from 90 → 120
        max_retries: int = 3         # ✅ added retry
    ):
        self.api_token = api_token or os.getenv("HF_TOKEN", "")
        self.generation_model = generation_model
        self.timeout = timeout
        self.max_retries = max_retries

        self.url = os.getenv(
            "HF_INFERENCE_V1_URL",
            "https://router.huggingface.co/v1/chat/completions"
        )


    # ------------------------------------------------
    # EXTRACT TEXT
    # ------------------------------------------------

    def _extract_text(self, payload: Any) -> str:

        if isinstance(payload, dict) and "choices" in payload:

            choices = payload.get("choices")

            if isinstance(choices, list) and choices:

                first = choices[0]

                if isinstance(first, dict):

                    message = first.get("message")

                    if isinstance(message, dict):

                        content = message.get("content")

                        if isinstance(content, str):

                            text = content.strip()

                            if text:
                                return text


        if isinstance(payload, dict):

            if "error" in payload:

                raise HFGenerationError(
                    str(payload.get("error"))
                )


        raise HFGenerationError("Invalid HF response format")


    # ------------------------------------------------
    # GENERATE TEXT
    # ------------------------------------------------

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256
    ) -> str:


        if not self.api_token:

            raise HFGenerationError(
                "HF token missing. Set HF_TOKEN environment variable."
            )


        headers = {

            "Authorization": f"Bearer {self.api_token}"

        }


        payload = {

            "model": self.generation_model,

            "messages": [

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            "max_tokens": max_new_tokens,

            "temperature": 0.1,

            "top_p": 0.9,

        }



        # ------------------------------------------------
        # RETRY LOOP
        # ------------------------------------------------

        for attempt in range(self.max_retries):

            try:

                response = requests.post(

                    self.url,

                    headers=headers,

                    json=payload,

                    timeout=self.timeout,

                )


                # ✅ HANDLE RATE LIMIT

                if response.status_code == 429:

                    wait_time = 10 * (attempt + 1)

                    print(f"HF rate limit. Waiting {wait_time}s...")

                    time.sleep(wait_time)

                    continue


                response.raise_for_status()


                data = response.json()

                text = self._extract_text(data)


                if text:

                    return text


            except requests.Timeout:

                print("HF timeout, retrying...")


            except requests.RequestException as e:

                print("HF request failed:", e)



            # wait before retry
            time.sleep(5)



        # ------------------------------------------------
        # FINAL FAIL
        # ------------------------------------------------

        raise HFGenerationError(

            "HF inference failed after retries"

        )
