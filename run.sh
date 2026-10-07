#!/usr/bin/env bash
set -e

PORT="${1:-8085}"

echo "================================================================="
echo "المملكة المغربية - بوابة تحرير وتدقيق المساطر الإدارية CPSV-AP"
echo "Morocco CPSV-AP 3.2.0 Administrative Portal & SHACL Validator"
echo "================================================================="

if [ "$1" == "--docker" ]; then
    echo "Building and launching container via standard Docker..."
    docker build -t morocco-cpsv-portal .
    docker rm -f morocco-cpsv-webui 2>/dev/null || true
    docker run -d --rm -p "${PORT}:8085" --name morocco-cpsv-webui morocco-cpsv-portal
    echo "Container running! Open http://localhost:${PORT}"
else
    echo "Launching portal natively on port ${PORT}..."
    if command -v uv >/dev/null 2>&1; then
        exec uv run --with rdflib --with pyshacl python3 src/morocco_cpsv_composer/server.py "${PORT}"
    else
        export PYTHONPATH="${PYTHONPATH:-.}:./src"
        exec python3 src/morocco_cpsv_composer/server.py "${PORT}"
    fi
fi
