import requests
import json

from app.core.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_case_summary(case_text: str):

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are an Indian legal expert.

Analyze the case and return ONLY valid JSON.

Format:

{{
  "sections": [
    {{
      "section_code": "420",
      "title": "Cheating",
      "punishment": "Up to 7 years imprisonment",
      "reason": "Why this section applies"
    }}
  ]
}}

Case:

{case_text}
"""

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload
    )

    data = response.json()

    print("\nFULL RESPONSE:\n")
    print(data)

    content = data["choices"][0]["message"]["content"]

    print("\nRAW CONTENT:\n")
    print(content)

    return json.loads(content)