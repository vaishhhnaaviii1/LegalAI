from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENROUTER_API_KEY: str
    INDIAN_KANOON_API_KEY: str

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()