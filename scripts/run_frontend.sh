#!/usr/bin/env bash
# ==============================================================================
# Intelligent QA - Script de Inicio del Frontend (Streamlit)
# ==============================================================================
set -e

# Posicionarse en la raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================================="
echo "  Iniciando Intelligent QA - Frontend UI (Streamlit)"
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

# 2. Comprobar existencia de .env
if [ ! -f ".env" ]; then
    echo "[WARN] No se encontró .env. Usando configuraciones predeterminadas."
fi

# 3. Configuración de entorno y ejecución
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
PORT="${FRONTEND_PORT:-8501}"

echo "[INFO] Lanzando Streamlit en el puerto ${PORT}..."
exec streamlit run src/frontend/app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --browser.gatherUsageStats false