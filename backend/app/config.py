from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GENWORLD_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "GenWorld"
    data_dir: Path = PROJECT_ROOT / "data"
    database_path: Path | None = None

    @property
    def resolved_database_path(self) -> Path:
        return self.database_path or self.data_dir / "genworld.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()

