from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://kma_user:kma_password@localhost:5432/kma"

    model_config = ConfigDict(env_file=".env")

settings = Settings()
