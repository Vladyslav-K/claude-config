#!/bin/bash

# Post-compact hook: Remind Claude to re-read all rules and memory
# Called by SessionStart hook with "compact" matcher

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║  ⚠️  CONTEXT WAS COMPACTED - RULES AND MEMORY MAY BE LOST            ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║                                                                      ║"
echo "║  BEFORE CONTINUING, YOU MUST RE-READ:                                ║"
echo "║                                                                      ║"
echo "║  1. RULES (use Glob + Read):                                         ║"
echo "║     - ~/.claude/CLAUDE.md                                            ║"
echo "║     - ~/.claude/rules/**/*.md                                        ║"
echo "║                                                                      ║"
echo "║  2. MEMORY (if exists in project):                                   ║"
echo "║     - .project-meta/memory/project-overview.md                       ║"
echo "║     - .project-meta/memory/recent-session.md                         ║"
echo "║     - .project-meta/memory/project-structure.md                      ║"
echo "║                                                                      ║"
echo "║  DO NOT CONTINUE WORKING until you've re-read these files!           ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Also output the memory if it exists
MEMORY_DIR=".project-meta/memory"

if [ -d "$MEMORY_DIR" ]; then
  echo "=== PROJECT MEMORY (auto-loaded) ==="
  echo ""

  if [ -f "$MEMORY_DIR/project-overview.md" ]; then
    echo "## Project Overview"
    cat "$MEMORY_DIR/project-overview.md"
    echo ""
  fi

  if [ -f "$MEMORY_DIR/recent-session.md" ]; then
    echo "## Recent Session Context"
    cat "$MEMORY_DIR/recent-session.md"
    echo ""
  fi

  echo "=== END OF PROJECT MEMORY ==="
  echo ""
fi

echo "IMPORTANT: Now use Glob to find ~/.claude/rules/**/*.md and Read each file!"
