from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Krishi Setu API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATA_RAW_DIR: Path = BASE_DIR / "data" / "raw"
    DATA_PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    ML_MODELS_DIR: Path = BASE_DIR / "ml_models"

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
