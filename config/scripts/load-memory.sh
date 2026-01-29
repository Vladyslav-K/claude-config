#!/bin/bash

# Load project memory files into Claude's context at session start
# This script is called by SessionStart hook

MEMORY_DIR=".project-meta/memory"

# Check if memory directory exists in current project
if [ ! -d "$MEMORY_DIR" ]; then
  exit 0
fi

echo "=== PROJECT MEMORY LOADED ==="
echo ""

# Read project overview first (most important)
if [ -f "$MEMORY_DIR/project-overview.md" ]; then
  echo "## Project Overview"
  cat "$MEMORY_DIR/project-overview.md"
  echo ""
fi

# Read recent session context (what we did last time)
if [ -f "$MEMORY_DIR/recent-session.md" ]; then
  echo "## Recent Session Context"
  cat "$MEMORY_DIR/recent-session.md"
  echo ""
fi

# Read changelog (history)
if [ -f "$MEMORY_DIR/changelog.md" ]; then
  echo "## Changelog (Recent History)"
  cat "$MEMORY_DIR/changelog.md"
  echo ""
fi

echo "=== END OF PROJECT MEMORY ==="
