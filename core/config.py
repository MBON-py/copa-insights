from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str | None = None
    app_env: str = "development"
    app_name: str = "Mestre dos Palpites"
    app_url: str = "http://localhost:8501"


settings = Settings()
