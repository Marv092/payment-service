from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")
    database_url: str
    migration_database_url: str
    auth_api_key: str
    rabbitmq_url: str
    log_level: str = "INFO"



settings = Settings()