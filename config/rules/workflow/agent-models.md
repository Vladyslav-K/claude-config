# Agent Model Configuration

Model assignment per agent role. Orchestrator reads this before spawning agents.

## How to Use

- `inherit` = omit `model` param → agent uses current chat model
- `sonnet`, `opus`, `haiku` = pass as `model` param to Task tool

## Configuration

| Role | Model   | Notes |
|------|---------|-------|
| researcher | sonnet  | Codebase search, pattern finding |
| analyzer | inherit | Vision + design analysis |
| implementer | inherit | Code implementation |
| validator | inherit | Code + design validation |
| planner | inherit | Screenshot + Figma analysis for planning |
| estimator | inherit | Task estimation |
| assembler | sonnet  | File merging |
