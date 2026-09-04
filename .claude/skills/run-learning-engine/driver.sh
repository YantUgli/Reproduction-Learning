#!/usr/bin/env bash
# Driver untuk Reproduction Learning Engine (backend FastAPI + frontend Next.js).
#
# Meluncurkan KEDUA server, menunggu keduanya sehat, lalu MENGGERAKKANNYA:
#   - curl smoke atas endpoint backend nyata (/health, /stats, /nodes)
#   - screenshot headless Chrome atas halaman frontend nyata (/, /placement, /review)
#
# Pemakaian (jalankan dari root repo):
#   .claude/skills/run-learning-engine/driver.sh up      # luncurkan + smoke + screenshot
#   .claude/skills/run-learning-engine/driver.sh smoke    # smoke+screenshot saja (server harus sudah jalan)
#   .claude/skills/run-learning-engine/driver.sh down      # matikan kedua server
#
# Log & screenshot mendarat di $OUT (default: scratchpad sesi bila ada, else ./.run-artifacts).
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUT="${RUN_OUT:-${CLAUDE_SCRATCHPAD:-$REPO/.run-artifacts}}"
# CORS backend hanya mengizinkan origin http://localhost:3000 (config.py FRONTEND_ORIGIN),
# jadi frontend WAJIB dibuka lewat nama "localhost", bukan 127.0.0.1 — kalau tidak, setiap
# fetch klien ke backend diblokir CORS dan halaman menampilkan "Tidak bisa menghubungi backend".
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
CHROME="${CHROME:-google-chrome}"
mkdir -p "$OUT"

wait_http() { # url max_tries
  local url="$1" tries="${2:-60}" code
  for ((i=1;i<=tries;i++)); do
    code=$(curl -s -o /dev/null -w '%{http_code}' "$url" 2>/dev/null)
    [ "$code" = "200" ] && return 0
    sleep 2
  done
  return 1
}

up() {
  echo "== launching backend (venv uvicorn) =="
  ( cd "$REPO/backend" && exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 ) \
    > "$OUT/backend.log" 2>&1 &
  echo $! > "$OUT/backend.pid"

  echo "== launching frontend (next dev) =="
  ( cd "$REPO/frontend" && exec npm run dev ) > "$OUT/frontend.log" 2>&1 &
  echo $! > "$OUT/frontend.pid"

  echo "== waiting for backend $BACKEND_URL/health =="
  wait_http "$BACKEND_URL/health" 30 || { echo "BACKEND FAILED"; tail -n 30 "$OUT/backend.log"; return 1; }
  echo "== waiting for frontend $FRONTEND_URL/ (next dev compiles on first hit) =="
  wait_http "$FRONTEND_URL/" 60 || { echo "FRONTEND FAILED"; tail -n 40 "$OUT/frontend.log"; return 1; }
  smoke
}

smoke() {
  local fail=0
  echo "== backend smoke =="
  for path in /health /stats /nodes; do
    code=$(curl -s -o "$OUT/resp$(echo "$path" | tr / _).json" -w '%{http_code}' "$BACKEND_URL$path")
    echo "  GET $path -> $code"
    [ "$code" = "200" ] || fail=1
  done
  echo "  /stats total_nodes: $(curl -s "$BACKEND_URL/stats" | "$REPO/backend/.venv/bin/python" -c 'import sys,json;print(json.load(sys.stdin)["total_nodes"])' 2>/dev/null)"

  echo "== frontend screenshots (headless chrome) =="
  # node = loop reproduksi inti (editor Monaco). n004 di-seed oleh load_nodes.py.
  for page in "home:/" "node:/node/n004_query_param_default" "placement:/placement" "review:/review"; do
    name="${page%%:*}"; route="${page#*:}"
    "$CHROME" --headless --no-sandbox --disable-gpu --hide-scrollbars \
      --virtual-time-budget=8000 --window-size=1280,900 \
      --screenshot="$OUT/frontend-$name.png" "$FRONTEND_URL$route" >/dev/null 2>&1
    if [ -s "$OUT/frontend-$name.png" ]; then
      echo "  $route -> $OUT/frontend-$name.png ($(stat -c%s "$OUT/frontend-$name.png") bytes)"
    else
      echo "  $route -> SCREENSHOT FAILED"; fail=1
    fi
  done
  echo "== artifacts in $OUT =="
  [ "$fail" = 0 ] && echo "SMOKE OK" || echo "SMOKE HAD FAILURES"
  return $fail
}

down() {
  for svc in backend frontend; do
    if [ -f "$OUT/$svc.pid" ]; then
      pid=$(cat "$OUT/$svc.pid")
      pkill -P "$pid" 2>/dev/null; kill "$pid" 2>/dev/null
      echo "killed $svc (pid $pid)"
    fi
  done
  pkill -f 'uvicorn app.main:app' 2>/dev/null
  pkill -f 'next dev' 2>/dev/null; pkill -f 'next-server' 2>/dev/null
  echo "down."
}

case "${1:-up}" in
  up) up ;;
  smoke) smoke ;;
  down) down ;;
  *) echo "usage: driver.sh {up|smoke|down}"; exit 2 ;;
esac
