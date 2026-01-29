#!/bin/bash
# Custom command for ccstatusline
# Calculates real context usage matching /context command

input=$(cat)

# Save full JSON for debugging
# echo "$input" | jq '.' > /tmp/cc_full.json
# echo "$input" | jq '.context_window' > /tmp/cc_context.json

# Constants (adjust if your config changes)
SYSTEM_PROMPT=2100
SYSTEM_TOOLS=17800
MCP_TOOLS=900
CUSTOM_AGENTS=1100
MEMORY_FILES=7200
SKILLS=100
# BASE_OVERHEAD = system prompt + tools + MCP + agents + memory files
BASE_OVERHEAD=$((SYSTEM_PROMPT + SYSTEM_TOOLS + MCP_TOOLS + CUSTOM_AGENTS + MEMORY_FILES + SKILLS))
AUTOCOMPACT_BUFFER=33000
CONTEXT_WINDOW_SIZE=200000

# Get values from JSON
CACHE_READ=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
CACHE_CREATE=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
INPUT_TOKENS=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
OUTPUT_TOKENS=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // 0')

# Calculate totals
CACHE_TOTAL=$((CACHE_READ + CACHE_CREATE + INPUT_TOKENS))

# Formula: TOTAL = cache (includes BASE) + output + AUTOCOMPACT
# output_tokens counts towards Messages in /context
if [ "$CACHE_TOTAL" -gt 0 ]; then
    TOTAL=$((CACHE_TOTAL + OUTPUT_TOKENS + AUTOCOMPACT_BUFFER))
else
    TOTAL=$((BASE_OVERHEAD + AUTOCOMPACT_BUFFER))
fi

# Cap at context window size
if [ "$TOTAL" -gt "$CONTEXT_WINDOW_SIZE" ]; then
    TOTAL=$CONTEXT_WINDOW_SIZE
fi

# Format output (k = thousands) - round UP
TOTAL_K=$(( (TOTAL + 999) / 1000 ))

# Calculate percentage - round UP
PERCENT=$(( (TOTAL * 100 + CONTEXT_WINDOW_SIZE - 1) / CONTEXT_WINDOW_SIZE ))

echo "${TOTAL_K}k (${PERCENT}%)"
