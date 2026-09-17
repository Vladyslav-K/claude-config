#!/bin/bash
# SessionStart / PostModelSwitch hook.
# Prints the working mode for the current model so the model sees it as context:
# Fable orchestrates and delegates code to the executor agent, any other model writes code itself.

INPUT=$(cat)

MODEL=$(echo "$INPUT" | jq -r '
  (.to_model // .model // "")
  | if type == "object" then (.display_name // .id // "") else . end
' 2>/dev/null)

# Without a model in the payload there is nothing reliable to report.
if [ -z "$MODEL" ] || [ "$MODEL" = "null" ]; then
  exit 0
fi

if echo "$MODEL" | grep -qi "fable"; then
  echo "Режим роботи: ОРКЕСТРАТОР (модель ${MODEL}). Діє секція «Оркестрація» з CLAUDE.md: аналіз, ТЗ і ревʼю - твої, код пише агент executor."
else
  echo "Режим роботи: ВИКОНАВЕЦЬ (модель ${MODEL}). Секція «Оркестрація» з CLAUDE.md НЕ діє: код пишеш сам, агента executor не запускаєш, з агентів дозволений лише Explore."
fi

exit 0
