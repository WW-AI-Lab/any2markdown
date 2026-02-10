#!/bin/bash

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3.13}"
VENV_DIR="${VENV_DIR:-.venv}"
PIP_INDEX_URL="${PIP_INDEX_URL:-https://repo.huaweicloud.com/repository/pypi/simple}"

echo "[INFO] Python: ${PYTHON_BIN}"
echo "[INFO] Venv: ${VENV_DIR}"
echo "[INFO] Index: ${PIP_INDEX_URL}"

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

pip install -i "${PIP_INDEX_URL}" --upgrade pip
pip install -i "${PIP_INDEX_URL}" -r requirements.txt

echo "[SUCCESS] Virtual environment ready: ${VENV_DIR}"
