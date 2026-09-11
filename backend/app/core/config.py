from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	database_url: str = "postgresql://kma_user:kma_password@localhost:5432/kma"

	class Config:
		env_file = ".env"

settings = Settings()
