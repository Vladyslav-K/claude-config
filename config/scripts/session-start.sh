#!/bin/bash

# Session start hook: Load persistent memory automatically
# Called by SessionStart hook with "startup" matcher

MEMORY_FILE=".project-meta/memory/persistent.md"

if [ -f "$MEMORY_FILE" ] && [ -s "$MEMORY_FILE" ]; then
  echo ""
  echo "╔══════════════════════════════════════════════════════════════════════╗"
  echo "║  🧠 PERSISTENT MEMORY DETECTED                                      ║"
  echo "╠══════════════════════════════════════════════════════════════════════╣"
  echo "║                                                                      ║"
  echo "║  BEFORE DOING ANYTHING ELSE, you MUST read:                         ║"
  echo "║     .project-meta/memory/persistent.md                              ║"
  echo "║                                                                      ║"
  echo "║  This file contains critical project-specific knowledge             ║"
  echo "║  that you need for this session.                                    ║"
  echo "║                                                                      ║"
  echo "╚══════════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "ACTION REQUIRED: Read .project-meta/memory/persistent.md NOW before responding to the user."
else
  echo "SessionStart:startup hook success: Success"
fi
