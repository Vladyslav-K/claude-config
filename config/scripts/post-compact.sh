#!/bin/bash

# Post-compact hook: Remind Claude to re-read all rules and persistent memory
# Called by SessionStart hook with "compact" matcher

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║  ⚠️  CONTEXT WAS COMPACTED - RULES MAY BE LOST                      ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║                                                                      ║"
echo "║  BEFORE CONTINUING, YOU MUST RE-READ:                                ║"
echo "║                                                                      ║"
echo "║  1. PERSISTENT MEMORY (read FIRST):                                 ║"
echo "║     - .project-meta/memory/persistent.md                            ║"
echo "║                                                                      ║"
echo "║  2. RULES (use Glob + Read):                                        ║"
echo "║     - ~/.claude/CLAUDE.md                                            ║"
echo "║     - ~/.claude/rules/**/*.md                                        ║"
echo "║                                                                      ║"
echo "║  DO NOT CONTINUE WORKING until you've re-read these files!           ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "IMPORTANT: First read .project-meta/memory/persistent.md, then use Glob to find ~/.claude/rules/**/*.md and Read each file!"
