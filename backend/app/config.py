from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "PALS API"
    environment: str = "development"
    database_url: str = "sqlite:///./pals.db"
    frontend_origins: str = "http://localhost:5173"
    judge0_base_url: str = "http://localhost:2358"
    judge0_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    request_timeout_seconds: float = 20
    bkt_initial: float = 0.20
    bkt_transition: float = 0.10
    bkt_guess: float = 0.20
    bkt_slip: float = 0.10
    intelligence_v2_enabled: bool = True
    intelligence_shadow_mode: bool = False
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def origins(self): return [x.strip() for x in self.frontend_origins.split(",") if x.strip()]

@lru_cache
def get_settings(): return Settings()
settings = get_settings()
