#!/bin/bash
input=$(cat)
echo "$input" | jq 'if .stop_hook_active == true then
  {continue: true}
else
  {
    decision: "block",
    reason: "Completion check (one pass, then released): walk through the original request point by point. For each point state done / partial / skipped with reason. If any point is partial or skipped and the user did not explicitly accept it — return and finish it. If truly complete — stop with the point-by-point confirmation."
  }
end'
