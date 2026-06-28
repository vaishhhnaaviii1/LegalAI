import re
from groq import AsyncGroq
# Import settings jo humne abhi banayi hai
from app.core.config import settings
from app.prompts.similarity_prompt import SIMILARITY_PROMPT

# Ab humein os.getenv ya boto3 ki zaroorat nahi, settings handle karega
client = AsyncGroq(
    api_key=settings.GROQ_API_KEY
)

async def llm_similarity_score(
    current_case: str,
    precedent_case: str,
) -> int:
    """
    Computes legal similarity using Groq LLM.
    """
    prompt = SIMILARITY_PROMPT.format(
        current_case=current_case,
        precedent_case=precedent_case,
    )

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=10,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert Indian Legal Research Assistant. "
                        "Always return ONLY a single integer between 0 and 100."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        answer = response.choices[0].message.content.strip()
        print(f"LLM Raw Response : {answer}")

        match = re.search(r"\d+", answer)
        if match:
            score = int(match.group())
            return max(0, min(score, 100))

        return 50

    except Exception as e:
        print(f"❌ LLM Similarity Error: {e}")
        return 50