#!/bin/bash
jq -n '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: "Before you act on this request: run the Discovery pass (see OWNERSHIP & DISCOVERY PROTOCOL in CLAUDE.md). If the request is non-trivial, answer the 4 discovery questions in your main response before any code. Match what this specific project actually does — do not apply generic defaults from rules/ if the project diverges. Prefer asking over guessing."
  }
}'
