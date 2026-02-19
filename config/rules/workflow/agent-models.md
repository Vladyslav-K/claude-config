# Agent Model Configuration

Model assignment per agent role. Orchestrator reads this before spawning agents.

## How to Use

- `inherit` = omit `model` param → agent uses current chat model
- `sonnet`, `opus`, `haiku` = pass as `model` param to Task tool

## Default (1 implementer per task)

| Role | Model | Notes |
|------|-------|-------|
| implementer | opus  | Researches + implements + self-reviews. Inherits chat model for best quality. |

## Optional / Special Roles

| Role | Model | Notes |
|------|-------|-------|
| estimator | opus  | Task estimation |
| assembler | opus  | File merging |
