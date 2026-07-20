#!/bin/bash

# Local Claude Code Statusline

# Read JSON from stdin into variable
INPUT=$(cat)

# Colors (ANSI)
CYAN='\033[38;5;116m'
BLUE='\033[94m'
MAGENTA='\033[95m'
YELLOW='\033[93m'
RESET='\033[0m'
BOLD='\033[1m'

# Parse JSON fields once
CWD_FULL=$(echo "$INPUT" | jq -r '.cwd // ""')
# Shorten home directory prefix to ~ for display only
CWD="$CWD_FULL"
if [[ -n "$HOME" ]] && [[ "$CWD" == "$HOME"* ]]; then
    CWD="~${CWD#$HOME}"
fi
MODEL_NAME=$(echo "$INPUT" | jq -r '.model.display_name // ""')
VERSION=$(echo "$INPUT" | jq -r '.version // ""')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

# ============================================
# Cache invalidation on new chat/clear
# ============================================
TRANSCRIPT_CACHE_FILE="$CLAUDE_DIR/.transcript-cache"
CONTEXT_CACHE_FILE="$CLAUDE_DIR/.context-cache"
CONTEXT_TOKENS_CACHE_FILE="$CLAUDE_DIR/.context-tokens-cache"

# Check if this is a new chat (transcript changed or empty)
CACHED_TRANSCRIPT=""
if [[ -f "$TRANSCRIPT_CACHE_FILE" ]]; then
    CACHED_TRANSCRIPT=$(cat "$TRANSCRIPT_CACHE_FILE")
fi

# If transcript is empty or different from cached - reset cache
if [[ -z "$TRANSCRIPT" ]] || [[ "$TRANSCRIPT" != "$CACHED_TRANSCRIPT" ]]; then
    rm -f "$CONTEXT_CACHE_FILE" "$CONTEXT_TOKENS_CACHE_FILE" 2>/dev/null
    if [[ -n "$TRANSCRIPT" ]]; then
        echo "$TRANSCRIPT" > "$TRANSCRIPT_CACHE_FILE"
    else
        rm -f "$TRANSCRIPT_CACHE_FILE" 2>/dev/null
    fi
fi

# ============================================
# LINE 1: Working directory
# ============================================

LINE1="${CYAN}${CWD}${RESET}"

# ============================================
# LINE 2: Git branch
# ============================================

GIT_BRANCH=""
if [[ -n "$CWD_FULL" ]] && [[ -d "$CWD_FULL" ]]; then
    GIT_BRANCH=$(git -C "$CWD_FULL" branch --show-current 2>/dev/null || echo "")
fi

if [[ -n "$GIT_BRANCH" ]]; then
    LINE2="${BLUE}${BOLD}⎇ ${GIT_BRANCH}${RESET}${BLUE}"
else
    LINE2="${BLUE}${BOLD}⎇ no git${RESET}${BLUE}"
fi

# ============================================
# LINE 3: Model | Version | Tokens
# ============================================

if [[ -n "$MODEL_NAME" ]]; then
    MODEL="$MODEL_NAME"
else
    MODEL="?"
fi

# Context tokens (same number as the token counter in the UI)
CTX_TOKENS_RAW=$(echo "$INPUT" | jq -r '(.context_window.total_input_tokens // 0) + (.context_window.total_output_tokens // 0)')

if [[ -z "$CTX_TOKENS_RAW" ]] || [[ "$CTX_TOKENS_RAW" == "0" ]]; then
    if [[ -f "$CONTEXT_TOKENS_CACHE_FILE" ]]; then
        CTX_TOKENS=$(cat "$CONTEXT_TOKENS_CACHE_FILE")
    else
        CTX_TOKENS="?"
    fi
else
    CTX_TOKENS="$CTX_TOKENS_RAW"
    echo "$CTX_TOKENS" > "$CONTEXT_TOKENS_CACHE_FILE"
fi

LINE3="${MAGENTA}${MODEL} | v${VERSION} | Tokens: ${CTX_TOKENS}${RESET}"

# ============================================
# LINE 4: Context | Cost
# ============================================

# Context
REMAINING_PCT=$(echo "$INPUT" | jq -r '.context_window.remaining_percentage // ""')

if [[ -z "$REMAINING_PCT" ]] || [[ "$REMAINING_PCT" == "null" ]] || [[ "$REMAINING_PCT" == "0" ]]; then
    if [[ -f "$CONTEXT_CACHE_FILE" ]]; then
        CONTEXT_PCT=$(cat "$CONTEXT_CACHE_FILE")
    else
        CONTEXT_PCT="?"
    fi
else
    CONTEXT_PCT=$(echo "$REMAINING_PCT" | awk '{
        result = $1;
        if (result < 0) result = 0;
        if (result > 100) result = 100;
        printf "%d", result;
    }')
    echo "$CONTEXT_PCT" > "$CONTEXT_CACHE_FILE"
fi

# Cost (direct from API)
# LC_ALL=C forces C locale for awk to use period as decimal separator
COST=$(echo "$INPUT" | jq -r '.cost.total_cost_usd // 0' | LC_ALL=C awk '{printf "%.2f", $1}')

# Lines changed
LINES_ADDED=$(echo "$INPUT" | jq -r '.cost.total_lines_added // 0')
LINES_REMOVED=$(echo "$INPUT" | jq -r '.cost.total_lines_removed // 0')

# Effort level
EFFORT_LEVEL=$(echo "$INPUT" | jq -r '.effort.level // empty')

# Rate limits: real server data from stdin (Pro/Max only, absent until first
# API response). Account-wide, so the cache survives new chats on purpose.
RATE_LIMITS_CACHE_FILE="$CLAUDE_DIR/.rate-limits-cache"
RATE_LIMITS_JSON=$(echo "$INPUT" | jq -c '.rate_limits // empty')
if [[ -n "$RATE_LIMITS_JSON" ]]; then
    echo "$RATE_LIMITS_JSON" > "$RATE_LIMITS_CACHE_FILE"
elif [[ -f "$RATE_LIMITS_CACHE_FILE" ]]; then
    RATE_LIMITS_JSON=$(cat "$RATE_LIMITS_CACHE_FILE")
fi

NOW_EPOCH=$(date +%s)
LIMIT_5H="?"
LIMIT_7D="?"
if [[ -n "$RATE_LIMITS_JSON" ]]; then
    FIVE_PCT=$(echo "$RATE_LIMITS_JSON" | jq -r '.five_hour.used_percentage // empty')
    FIVE_RESET=$(echo "$RATE_LIMITS_JSON" | jq -r '.five_hour.resets_at // empty')
    FIVE_RESET=${FIVE_RESET%%.*}
    # Show only while the window is still running: a past resets_at means
    # the cached percentage is stale and no longer true
    if [[ -n "$FIVE_PCT" ]] && [[ -n "$FIVE_RESET" ]] && (( FIVE_RESET > NOW_EPOCH )); then
        REMAIN_S=$((FIVE_RESET - NOW_EPOCH))
        REMAIN_H=$((REMAIN_S / 3600))
        REMAIN_M=$(( (REMAIN_S % 3600) / 60 ))
        if (( REMAIN_H > 0 )); then
            FIVE_LEFT=$(printf '%dh%02dm' "$REMAIN_H" "$REMAIN_M")
        else
            FIVE_LEFT="${REMAIN_M}m"
        fi
        LIMIT_5H="$(LC_ALL=C printf '%.0f' "$FIVE_PCT")% (${FIVE_LEFT})"
    fi

    SEVEN_PCT=$(echo "$RATE_LIMITS_JSON" | jq -r '.seven_day.used_percentage // empty')
    SEVEN_RESET=$(echo "$RATE_LIMITS_JSON" | jq -r '.seven_day.resets_at // empty')
    SEVEN_RESET=${SEVEN_RESET%%.*}
    if [[ -n "$SEVEN_PCT" ]] && [[ -n "$SEVEN_RESET" ]] && (( SEVEN_RESET > NOW_EPOCH )); then
        SEVEN_AT=$(LC_ALL=C date -r "$SEVEN_RESET" '+%a %H:%M')
        LIMIT_7D="$(LC_ALL=C printf '%.0f' "$SEVEN_PCT")% (${SEVEN_AT})"
    fi
fi

EXTRAS=""
if [[ -n "$EFFORT_LEVEL" ]]; then
    EXTRAS="${EFFORT_LEVEL}"
fi
LIMITS_DISPLAY="5h: ${LIMIT_5H} | 7d: ${LIMIT_7D}"
if [[ -n "$EXTRAS" ]]; then
    EXTRAS="${EXTRAS} | ${LIMITS_DISPLAY}"
else
    EXTRAS="${LIMITS_DISPLAY}"
fi

SUFFIX=""
[[ -n "$EXTRAS" ]] && SUFFIX=" | ${EXTRAS}"

LINE4="${YELLOW}Context: ${CONTEXT_PCT}% | +${LINES_ADDED} -${LINES_REMOVED} | \$${COST}${SUFFIX}${RESET}"

# ============================================
# OUTPUT
# ============================================

echo -e "$LINE1"
echo -e "$LINE2"
echo -e "$LINE3"
echo -e "$LINE4"
