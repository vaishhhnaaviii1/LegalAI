import requests
from app.core.config import settings


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_case_summary(case_text: str):

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    Analyze this legal case.

    Give:
    1. Summary
    2. Possible IPC Sections
    3. Legal reasoning

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

    return data["choices"][0]["message"]["content"]