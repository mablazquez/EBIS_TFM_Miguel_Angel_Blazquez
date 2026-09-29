"""
Módulo de Configuración Central y Gestor de Prompts Externalizados.
"""

from pathlib import Path
from typing import Dict, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Configuración global del sistema con soporte para mayúsculas y minúsculas."""
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Credenciales y Modelo LLM
    gemini_api_key: str = Field(default="", description="API Key de Google Gemini")
    llm_model: str = Field(default="gemini-3.8-flash", description="Modelo LLM")

    # Servidor
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    frontend_port: int = Field(default=8501)
    api_base_url: str = Field(default="http://localhost:8000")

    # Logging y Entorno
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")

    # Rutas
    prompts_dir: Path = Field(default=PROJECT_ROOT / "data" / "prompts")

    # Aliases de compatibilidad para accesos en mayúsculas
    @property
    def LLM_MODEL(self) -> str:
        return self.llm_model

    @property
    def GEMINI_API_KEY(self) -> str:
        return self.gemini_api_key

    @property
    def LOG_LEVEL(self) -> str:
        return self.log_level

    @property
    def ENVIRONMENT(self) -> str:
        return self.environment


class PromptLoader:
    """Carga y valida los prompts externalizados en data/prompts/."""

    REQUIRED_PROMPT_FILES: List[str] = [
        "classifier_guardrail.txt",
        "inconsistencies.txt",
        "standards.txt",
        "test_cases.txt",
        "reverse_engineering.txt",
        "unit_tests.txt"
    ]

    def __init__(self, prompts_directory: Path) -> None:
        self.prompts_directory = prompts_directory
        self._cache: Dict[str, str] = {}

    def get_prompt(self, filename: str) -> str:
        if filename in self._cache:
            return self._cache[filename]

        prompt_path = self.prompts_directory / filename
        if not prompt_path.is_file():
            raise FileNotFoundError(f"[ERROR] No existe el prompt: {prompt_path}")

        content = prompt_path.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"[ERROR] El prompt {filename} está vacío.")

        self._cache[filename] = content
        return content

    def validate_all_prompts(self) -> None:
        for filename in self.REQUIRED_PROMPT_FILES:
            self.get_prompt(filename)


settings = Settings()
prompt_loader = PromptLoader(prompts_directory=settings.prompts_dir)