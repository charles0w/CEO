#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/backend/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python3}"
fi

log() {
  printf '\n[validate] %s\n' "$1"
}

log "checking git whitespace"
git -C "$ROOT" diff --check

log "compiling backend Python"
"$PYTHON_BIN" -m py_compile \
  "$ROOT/backend/config.py" \
  "$ROOT/backend/main.py" \
  "$ROOT/backend/benchmarks/cases.py" \
  "$ROOT/backend/services/structured_output.py" \
  "$ROOT/backend/services/voice_service.py" \
  "$ROOT/backend/services/llm_provider.py" \
  "$ROOT/backend/services/llm_service.py" \
  "$ROOT/backend/services/ollama_service.py"

log "checking structured JSON helper"
(
  cd "$ROOT/backend"
  "$PYTHON_BIN" - <<'PY'
from services.structured_output import parse_json_object

required = ["plan", "risks", "next_action"]
cases = [
    ('{"plan":["a"],"risks":["b"],"next_action":"c"}', False),
    ('```json\n{"plan":["a"],"risks":["b"],"next_action":"c"}\n```', True),
    ('Here: {"plan":["a"],"risks":["b"],"next_action":"c"}', True),
]
for text, repaired in cases:
    result = parse_json_object(text, required)
    assert result.valid, result
    assert result.repaired is repaired, result
print("structured_output ok")
PY
)

log "checking mobile dependencies"
(
  cd "$ROOT/mobile"
  if [[ ! -d node_modules ]]; then
    npm ci --legacy-peer-deps --no-audit
  fi
  npm audit --omit=dev --audit-level=moderate
  npx tsc --noEmit --pretty false
  npx expo install --check
  npx expo config --json >/tmp/ceo-expo-config-validate.json
)

log "running Expo Doctor"
(
  cd "$ROOT/mobile"
  set +e
  npx expo-doctor >/tmp/ceo-expo-doctor.txt 2>&1
  status=$?
  set -e
  if [[ $status -ne 0 ]]; then
    if grep -q "Unmaintained: expo-av" /tmp/ceo-expo-doctor.txt && grep -q "1 check failed" /tmp/ceo-expo-doctor.txt; then
      cat /tmp/ceo-expo-doctor.txt
      printf '\n[validate] Expo Doctor has only the known expo-av maintenance warning.\n'
    else
      cat /tmp/ceo-expo-doctor.txt
      exit "$status"
    fi
  else
    cat /tmp/ceo-expo-doctor.txt
  fi
)

if [[ "${RUN_EXPO_WEB_EXPORT:-1}" != "0" ]]; then
  log "exporting Expo web bundle"
  rm -rf /tmp/ceo-expo-web-export
  (
    cd "$ROOT/mobile"
    npx expo export --platform web --output-dir /tmp/ceo-expo-web-export
  )
fi

log "all checks passed"
