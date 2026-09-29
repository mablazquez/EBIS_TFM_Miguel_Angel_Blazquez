#!/usr/bin/env bash
# ==============================================================================
# Intelligent QA - Script de Inicio del Backend (FastAPI + Uvicorn)
# ==============================================================================
set -e

# Posicionarse en la raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================================="
echo "  Iniciando Intelligent QA - Backend API (FastAPI)"
echo "=========================================================="

# 1. Comprobación y activación de entorno virtual
if [ -d ".venv" ]; then
    echo "[INFO] Activando entorno virtual (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "[INFO] Activando entorno virtual (venv)..."
    source venv/bin/activate
else
    echo "[WARN] No se detectó entorno virtual en .venv o venv. Se usará el Python del sistema."
fi

# 2. Verificación de archivo de entorno
if [ ! -f ".env" ]; then
    echo "[ERROR] No se encontró el archivo .env en la raíz del proyecto."
    echo "[ACTION] Copia .env.example a .env y configura tu GEMINI_API_KEY:"
    echo "         cp .env.example .env"
    exit 1
fi

# 3. Exportar variables de entorno si procede y configurar PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

HOST="${BACKEND_HOST:-0.0.0.0}"
PORT="${BACKEND_PORT:-8000}"

echo "[INFO] Verificando integridad de prompts en data/prompts/..."
python -c "from src.core.config import prompt_loader; prompt_loader.validate_all_prompts(); print('[OK] Prompts validados correctamente.')"

echo "[INFO] Lanzando Uvicorn en http://${HOST}:${PORT}..."
exec uvicorn src.backend.main:app --host "$HOST" --port "$PORT" --reload