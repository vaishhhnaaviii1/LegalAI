import requests
from app.core.config import settings


def search_similar_cases(query: str):

    url = "https://api.indiankanoon.org/search/"

    headers = {
        "Authorization": f"Token {settings.INDIAN_KANOON_API_KEY}"
    }

    params = {
        "formInput": query
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    return response.json()