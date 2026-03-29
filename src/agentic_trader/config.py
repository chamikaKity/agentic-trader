from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    cryptopanic_api_key: str

    model_config = {"env_file": ".env"}


settings = Settings()  # type: ignore[call-arg]  # pydantic-settings populates fields from env vars
