# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ----------------------------
    # Application Keys and Tokens
    # ----------------------------
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    AZURE_OPENAI_API_KEY: str
    TEAMS_WEBHOOK_URL: str
    AZURE_MAPS_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="allow"
    )

# Instantiate settings
settings = Settings()  # ty:ignore[missing-argument]
