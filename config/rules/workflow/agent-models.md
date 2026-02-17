# Agent Model Configuration

Model assignment per agent role. Orchestrator reads this before spawning agents.

## How to Use

- `inherit` = omit `model` param → agent uses current chat model
- `sonnet`, `opus`, `haiku` = pass as `model` param to Task tool

## Configuration

| Role | Model  | Notes |
|------|--------|-------|
| researcher | sonnet | Codebase search, pattern finding |
| analyzer | opus   | Vision + design analysis |
| implementer | sonnet | Code implementation |
| validator | opus   | Code + design validation |
| planner | opus   | Screenshot + Figma analysis for planning |
| estimator | opus   | Task estimation |
| assembler | sonnet | File merging |
