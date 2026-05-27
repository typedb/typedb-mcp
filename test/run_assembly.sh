#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.test.yml)

cleanup() {
    if [[ "${KEEP_LOGS:-0}" == "1" ]]; then
        echo "---typedb logs---"
        docker compose "${COMPOSE_FILES[@]}" logs typedb || true
        echo "---typedb-mcp logs---"
        docker compose "${COMPOSE_FILES[@]}" logs typedb-mcp || true
    fi
    docker compose "${COMPOSE_FILES[@]}" down -v
}
trap cleanup EXIT

docker compose "${COMPOSE_FILES[@]}" up -d --build

wait_for() {
    local name="$1" url="$2"
    echo "Waiting for $name at $url..."
    for i in $(seq 1 60); do
        # Accept any HTTP response (even an error status) as proof the app is up; a docker-published port accepts TCP connects before the app inside is listening, so a TCP-only check would pass too early
        if curl -s -o /dev/null --max-time 2 "$url"; then
            echo "$name is ready"
            return 0
        fi
        sleep 1
    done
    echo "$name did not become ready in time" >&2
    KEEP_LOGS=1
    return 1
}

wait_for "typedb" "http://localhost:8000"
wait_for "typedb-mcp" "http://localhost:8001/mcp"

uv run python test/assembly.py
