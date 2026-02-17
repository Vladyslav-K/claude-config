# Agent Model Configuration

Model assignment per agent role. Orchestrator reads this before spawning agents.

## How to Use

- `inherit` = omit `model` param → agent uses current chat model
- `sonnet`, `opus`, `haiku` = pass as `model` param to Task tool

## Default Chain (2 agents)

| Role | Model | Notes |
|------|--------|-------|
| implementer | opus | Researches + implements. Inherits chat model for best quality. |
| validator | opus | Independent validation. Inherits chat model for thorough review. |

## Optional / Special Roles

| Role | Model | Notes |
|------|--------|-------|
| planner | opus | Screenshot + Figma analysis for task planning |
| estimator | opus | Task estimation |
| assembler | sonnet | File merging |
