#!/bin/bash

# Post-compact hook: Remind Claude to re-read all rules
# Called by SessionStart hook with "compact" matcher

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║  ⚠️  CONTEXT WAS COMPACTED - RULES MAY BE LOST                      ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║                                                                      ║"
echo "║  BEFORE CONTINUING, YOU MUST RE-READ:                                ║"
echo "║                                                                      ║"
echo "║  RULES (use Glob + Read):                                           ║"
echo "║     - ~/.claude/CLAUDE.md                                            ║"
echo "║     - ~/.claude/rules/**/*.md                                        ║"
echo "║                                                                      ║"
echo "║  DO NOT CONTINUE WORKING until you've re-read these files!           ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "IMPORTANT: Now use Glob to find ~/.claude/rules/**/*.md and Read each file!"
