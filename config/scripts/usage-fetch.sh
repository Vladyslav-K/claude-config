#!/bin/bash

# Fetches subscription usage windows into a local cache for the statusline.
# Runs detached from statusline.sh so the statusline itself never waits on the
# network - it only reads the cache file this script writes.

set -u

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CREDENTIALS_FILE="$CLAUDE_DIR/.credentials.json"
CACHE_FILE="$CLAUDE_DIR/.usage-cache.json"
LOCK_DIR="$CLAUDE_DIR/.usage-fetch.lock"
API_URL="https://api.anthropic.com/api/oauth/usage"
LOCK_STALE_SECONDS=120

# GNU stat first: its -f form prints file system text before failing
file_mtime() {
    stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null
}

# One fetch at a time across parallel sessions; mkdir is atomic
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    LOCK_AT=$(file_mtime "$LOCK_DIR")
    if [[ -n "$LOCK_AT" ]] && (( $(date +%s) - LOCK_AT > LOCK_STALE_SECONDS )); then
        rmdir "$LOCK_DIR" 2>/dev/null
    fi
    exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

[[ -f "$CREDENTIALS_FILE" ]] || exit 0

TOKEN=$(jq -r '.claudeAiOauth.accessToken // empty' "$CREDENTIALS_FILE" 2>/dev/null)
[[ -n "$TOKEN" ]] || exit 0

TMP_FILE=$(mktemp "${TMPDIR:-/tmp}/claude-usage.XXXXXX") || exit 0

# The token goes in through --config on stdin, not argv, so it stays out of ps
HTTP_CODE=$(printf 'header = "Authorization: Bearer %s"\n' "$TOKEN" \
    | curl -sS --config - \
        -o "$TMP_FILE" -w '%{http_code}' --max-time 10 \
        -H 'Content-Type: application/json' \
        -H 'anthropic-beta: oauth-2025-04-20' \
        "$API_URL" 2>/dev/null)

# Keep the previous cache on any failure: stale numbers beat no numbers
if [[ "$HTTP_CODE" == "200" ]] && jq -e 'type == "object"' "$TMP_FILE" >/dev/null 2>&1; then
    mv "$TMP_FILE" "$CACHE_FILE"
    chmod 600 "$CACHE_FILE" 2>/dev/null
else
    rm -f "$TMP_FILE"
fi
