#!/bin/bash
jq -n '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: "Before you act on this request: internally run the Discovery pass (see OWNERSHIP & DISCOVERY PROTOCOL in CLAUDE.md) — think through the 4 questions without outputting them as a Q&A block in the chat. In the chat, output only: a concise action plan (1-5 sentences on what you will do) and any genuine open questions that need user input. For complex tasks, present a proper plan for approval per .claude/rules/task-execution.md. Match what this specific project actually does — do not apply generic defaults from rules/ if the project diverges. Prefer asking over guessing."
  }
}'
