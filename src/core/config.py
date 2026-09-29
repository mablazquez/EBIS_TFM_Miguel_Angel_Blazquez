"""Configuración centralizada y gestor estricto de prompts externos.

Este módulo carga variables de entorno mediante Pydantic Settings y ofrece un
PromptLoader desacoplado que prohíbe cualquier fallback hardcodeado.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación validada en tiempo de arranque."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys & Modelo LLM (Regla 2: gemini-3.8-flash)
    GEMINI_API_KEY: str = Field(
        ...,
        description="Clave de acceso a la API de Google Gemini.",
    )
    MODEL_NAME: str = Field(
        default="gemini-3.8-flash",
        description="Identificador estricto del modelo LLM de Google.",
    )

    # Configuración de Red
    BACKEND_HOST: str = Field(default="0.0.0.0")
    BACKEND_PORT: int = Field(default=8000)
    FRONTEND_PORT: int = Field(default=8501)

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
    )
    ENVIRONMENT: Literal["development", "production", "test"] = Field(
        default="development",
    )

    # Directorios Base del Proyecto
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    PROMPTS_DIR: Path = DATA_DIR / "prompts"


class PromptLoader:
    """Cargador centralizado y estricto de plantillas de prompts externos.

    Garantiza el cumplimiento de la Regla 1: ningún prompt puede estar
    hardcodeado en Python. Si el archivo no existe, falla inmediatamente sin fallback.
    """

    def __init__(self, prompts_directory: Path) -> None:
        self._prompts_directory = prompts_directory

    @lru_cache(maxsize=32)
    def load(self, prompt_filename: str) -> str:
        """Carga el contenido de un prompt externo desde el directorio data/prompts/.

        Args:
            prompt_filename: Nombre del archivo dentro de data/prompts/ (ej. 'classifier_guardrail.txt').

        Returns:
            Contenido textual completo del prompt.

        Raises:
            FileNotFoundError: Si el archivo no existe o no es accesible.
            ValueError: Si el archivo está vacío.
        """
        prompt_path = self._prompts_directory / prompt_filename

        if not prompt_path.is_file():
            raise FileNotFoundError(
                f"[REGLA 1 VIOLADA] El archivo de prompt requerido '{prompt_filename}' "
                f"NO fue encontrado en '{self._prompts_directory}'. Está estrictamente "
                "prohibido definir cadenas de prompts por defecto en el código Python."
            )

        content = prompt_path.read_text(encoding="utf-8").strip()

        if not content:
            raise ValueError(
                f"[ERROR DE PROMPT] El archivo de prompt '{prompt_filename}' existe pero está vacío."
            )

        return content

    def clear_cache(self) -> None:
        """Limpia la caché de prompts (útil para pruebas y recarga en caliente)."""
        self.load.cache_clear()


# Instancias Singleton para reutilización en todo el proyecto
settings = Settings()
prompt_loader = PromptLoader(prompts_directory=settings.PROMPTS_DIR)