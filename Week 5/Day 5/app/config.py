from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "http://localhost:8000"
    openrouter_app_name: str = "Web3Geeks Capstone Agent"
    tool_timeout_seconds: float = 4.0
    model_timeout_seconds: float = 45.0
    max_model_retries: int = 2
    log_level: str = "INFO"
    database_path: str = str(ROOT / "data" / "capstone.db")
    company_profile_path: str = str(ROOT / "data" / "company_profile.md")
    log_path: str = str(ROOT / "logs" / "agent.log")
    model_cost_input_per_million: float = 0.40
    model_cost_output_per_million: float = 1.60

    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")

settings = Settings()
