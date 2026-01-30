#!/bin/bash

# Local Claude Code Statusline

# Read JSON from stdin into variable
INPUT=$(cat)

# Debug: log raw input to file (remove after debugging)
echo "$INPUT" > /tmp/statusline-debug.json

# Colors (ANSI)
BLUE='\033[94m'
MAGENTA='\033[95m'
YELLOW='\033[93m'
RESET='\033[0m'
BOLD='\033[1m'

# Parse JSON fields once
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
MODEL_NAME=$(echo "$INPUT" | jq -r '.model.display_name // ""')
VERSION=$(echo "$INPUT" | jq -r '.version // ""')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

# ============================================
# Cache invalidation on new chat/clear
# ============================================
TRANSCRIPT_CACHE_FILE="$CLAUDE_DIR/.transcript-cache"
CONTEXT_CACHE_FILE="$CLAUDE_DIR/.context-cache"

# Check if this is a new chat (transcript changed or empty)
CACHED_TRANSCRIPT=""
if [[ -f "$TRANSCRIPT_CACHE_FILE" ]]; then
    CACHED_TRANSCRIPT=$(cat "$TRANSCRIPT_CACHE_FILE")
fi

# If transcript is empty or different from cached - reset cache
if [[ -z "$TRANSCRIPT" ]] || [[ "$TRANSCRIPT" != "$CACHED_TRANSCRIPT" ]]; then
    rm -f "$CONTEXT_CACHE_FILE" 2>/dev/null
    if [[ -n "$TRANSCRIPT" ]]; then
        echo "$TRANSCRIPT" > "$TRANSCRIPT_CACHE_FILE"
    else
        rm -f "$TRANSCRIPT_CACHE_FILE" 2>/dev/null
    fi
fi

# ============================================
# LINE 1: Git branch | Working directory
# ============================================

GIT_BRANCH=""
if [[ -n "$CWD" ]] && [[ -d "$CWD" ]]; then
    GIT_BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "")
fi

if [[ -n "$GIT_BRANCH" ]]; then
    LINE1="${BLUE}${BOLD}⎇ ${GIT_BRANCH}${RESET}${BLUE} | ${CWD}${RESET}"
else
    LINE1="${BLUE}${BOLD}⎇ no git${RESET}${BLUE} | ${CWD}${RESET}"
fi

# ============================================
# LINE 2: Model | Version | Tokens
# ============================================

if [[ -n "$MODEL_NAME" ]]; then
    MODEL="$MODEL_NAME"
else
    MODEL="?"
fi

TOTAL_TOKENS=0
if [[ -n "$TRANSCRIPT" ]] && [[ -f "$TRANSCRIPT" ]]; then
    TOTAL_TOKENS=$(grep -oE '"(input_tokens|output_tokens|cache_read_input_tokens|cache_creation_input_tokens)":[0-9]+' "$TRANSCRIPT" 2>/dev/null | \
        grep -oE '[0-9]+$' | \
        awk '{sum+=$1} END {print sum+0}')
fi

if [[ $TOTAL_TOKENS -ge 1000000 ]]; then
    MILLIONS=$((TOTAL_TOKENS / 1000000))
    REMAINDER=$(( (TOTAL_TOKENS % 1000000) / 100000 ))
    FORMATTED_TOKENS="${MILLIONS}.${REMAINDER}M"
elif [[ $TOTAL_TOKENS -ge 1000 ]]; then
    THOUSANDS=$((TOTAL_TOKENS / 1000))
    REMAINDER=$(( (TOTAL_TOKENS % 1000) / 100 ))
    FORMATTED_TOKENS="${THOUSANDS}.${REMAINDER}K"
else
    FORMATTED_TOKENS="$TOTAL_TOKENS"
fi

LINE2="${MAGENTA}${MODEL} | v${VERSION} | Tokens: ${FORMATTED_TOKENS}${RESET}"

# ============================================
# LINE 3: Context | Cost
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
        result = $1 - 16.5 - 1;
        if (result < 0) result = 0;
        printf "%d", result;
    }')
    echo "$CONTEXT_PCT" > "$CONTEXT_CACHE_FILE"
fi

# Cost (direct from API)
COST_RAW=$(echo "$INPUT" | jq -r '.cost.total_cost_usd // 0')
COST=$(printf "%.2f" "$COST_RAW")

# Lines changed
LINES_ADDED=$(echo "$INPUT" | jq -r '.cost.total_lines_added // 0')
LINES_REMOVED=$(echo "$INPUT" | jq -r '.cost.total_lines_removed // 0')

LINE3="${YELLOW}Context: ${CONTEXT_PCT}% | +${LINES_ADDED} -${LINES_REMOVED} | \$${COST}${RESET}"

# ============================================
# OUTPUT
# ============================================

echo -e "$LINE1"
echo -e "$LINE2"
echo -e "$LINE3"
