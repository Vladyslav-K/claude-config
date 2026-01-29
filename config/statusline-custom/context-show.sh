#!/bin/bash
input=$(cat)

REMAINING_PERCENTAGE=$(echo "$input" | jq -r '.context_window.remaining_percentage // 100')

echo "${REMAINING_PERCENTAGE}%"