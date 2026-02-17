# Figma-to-Code Translation Rules

**These rules have been moved to agent skills for context optimization.**

Agents receive Figma-to-code instructions via:
- `/agent:analyzer` — Figma JSON processing, dimension extraction, color tables
- `/agent:implementer` — Dimension conversion to Tailwind, NO approximations rule

The orchestrator does not need these rules (pure manager role).
