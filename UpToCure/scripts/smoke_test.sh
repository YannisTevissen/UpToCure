#!/usr/bin/env bash
# Local end-to-end smoke test for UpToCure.
#
# Starts the gunicorn production server on a free port, waits for /healthz to
# return 200, then exercises the public HTTP API. Fails the build if any check
# is broken. Intended to be run locally before deploying, and by CI.
#
# Usage:
#   bash scripts/smoke_test.sh             # uses pdm to install deps
#   PORT=8123 bash scripts/smoke_test.sh   # override the port

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8765}"
HOST="127.0.0.1"
BASE="http://${HOST}:${PORT}"
LOG="$(mktemp)"

GREEN="\033[0;32m"; RED="\033[0;31m"; YELLOW="\033[0;33m"; NC="\033[0m"

log_step() { printf "${YELLOW}==>${NC} %s\n" "$1"; }
log_ok()   { printf "${GREEN}✓${NC}  %s\n" "$1"; }
log_err()  { printf "${RED}✗${NC}  %s\n" "$1"; }

# 1. Make sure dependencies are installed -------------------------------------
if command -v pdm >/dev/null 2>&1; then
    log_step "Installing dependencies (pdm install -d)"
    pdm install -d >/dev/null
    RUN="pdm run"
else
    log_step "pdm not found, using existing Python interpreter"
    RUN=""
fi

# 2. Run pytest ---------------------------------------------------------------
log_step "Running unit tests"
if $RUN pytest -q; then
    log_ok "pytest"
else
    log_err "pytest failed"
    exit 1
fi

# 3. Boot the server ----------------------------------------------------------
log_step "Booting gunicorn on $BASE"
$RUN gunicorn --bind "${HOST}:${PORT}" --workers 1 --access-logfile - "src.app:app" \
    >"$LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
    if kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    if [ "${KEEP_LOG:-0}" = "1" ]; then
        printf "Server log: %s\n" "$LOG"
    else
        rm -f "$LOG"
    fi
}
trap cleanup EXIT

# Wait until /healthz answers (up to ~10s)
for _ in $(seq 1 50); do
    if curl -sf "${BASE}/healthz" >/dev/null; then
        break
    fi
    sleep 0.2
done

if ! curl -sf "${BASE}/healthz" >/dev/null; then
    log_err "Server failed to come up. Log follows:"
    cat "$LOG"
    exit 1
fi
log_ok "Server is up"

# 4. Assert endpoints ---------------------------------------------------------
assert_status() {
    local path="$1"; shift
    local expected="$1"; shift
    local method="${1:-GET}"
    local data="${2:-}"
    local status
    if [ "$method" = "POST" ]; then
        status=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d "$data" "${BASE}${path}")
    else
        status=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}${path}")
    fi
    if [ "$status" = "$expected" ]; then
        log_ok "$method $path → $status"
    else
        log_err "$method $path expected $expected got $status"
        cat "$LOG"
        exit 1
    fi
}

assert_status "/healthz" 200
assert_status "/" 200
assert_status "/fr/" 200
assert_status "/methodology" 200
assert_status "/fr/methodology" 200
assert_status "/methodology.html" 200
assert_status "/robots.txt" 200
assert_status "/sitemap.xml" 200
assert_status "/search" 200
assert_status "/search?q=disease" 200
assert_status "/this-does-not-exist" 404
assert_status "/api" 200
assert_status "/api/reports?lang=en" 200
assert_status "/api/reports?lang=xx" 400
assert_status "/api/reports/en/not-a-real-disease" 404
assert_status "/api/request-report" 400 POST '{}'
assert_status "/api/request-report" 200 POST '{"disease": "Smoke Test Disease"}'

# Detail endpoint + report page — pick the first real slug from the listing
SLUG=$(curl -s "${BASE}/api/reports?lang=en" | python -c "import sys, json; data=json.load(sys.stdin); print((data.get('reports') or [{}])[0].get('slug',''))")
if [ -n "$SLUG" ]; then
    assert_status "/api/reports/en/${SLUG}" 200
    assert_status "/reports/en/${SLUG}" 200
    assert_status "/reports/fr/${SLUG}" 200
fi

# Spot-check that the home page actually contains a server-rendered link
HOME_BODY=$(curl -s "${BASE}/")
if printf '%s' "$HOME_BODY" | grep -q "/reports/en/"; then
    log_ok "Home page contains canonical report links"
else
    log_err "Home page is missing server-rendered report links"
    exit 1
fi

# Spot-check sitemap content
SITEMAP_BODY=$(curl -s "${BASE}/sitemap.xml")
if printf '%s' "$SITEMAP_BODY" | grep -q "<urlset"; then
    log_ok "Sitemap is valid XML"
else
    log_err "Sitemap is malformed"
    exit 1
fi

log_ok "All smoke checks passed"
