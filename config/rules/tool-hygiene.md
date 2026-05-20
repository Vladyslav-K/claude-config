# Tool Hygiene

**Scope.** This file collects discipline rules for how I use tools — Bash, AskUserQuestion, and any future tools where the *form* of usage (not its correctness) can degrade the experience: noisy output, truncated previews, ceremony around results, etc. When adding a new block here, keep the same shape: name the tool / surface, name the failure mode, give the correct form, give the rationale.

---

## Bash & Output Hygiene

- **Do NOT redirect command output to a temp file just to read it back with `tail`/`head`.** The pattern `cmd > /tmp/foo.log 2>&1; tail -N /tmp/foo.log` adds an extra step and leaves a stale artifact that exists only to enable the `tail`. The correct form when you do need to trim output is `cmd 2>&1 | tail -N`. Use a real temp file ONLY when you genuinely need to preserve the full log for later analysis (rare — and usually means the command should be quieter at the source).
- **Do NOT pipe to `tail` by default.** The Bash tool already truncates very large outputs to a preview. For most commands the raw output is fine. Reach for `| tail -N` ONLY when the command is known to produce a huge stream of low-value lines (e.g., `prettier --write` listing every file) AND the meaningful info is at the end. If errors can surface near the top, `tail` will hide them — prefer fixing the noisy command itself (see the Prettier `--log-level=warn` rule in CLAUDE.md → Post-Task Requirements) over masking the noise with `tail`.
- **Do NOT add `echo "EXIT=$?"` after a command.** The Bash tool surfaces exit codes by itself; the extra echo is ceremony, not signal. The only legitimate use is when chaining commands with `;` and you specifically need to see the intermediate exit code — which is itself a smell, prefer `&&` chaining or separate calls.
- **Principle.** If a command is too noisy to read, the right fix is at the source (a quieter flag, a better script) — not a downstream `tail`/`grep`/redirect that loses information. Reach for output filtering only when fixing the source is genuinely not in scope.

---

## AskUserQuestion Hygiene

- **NEVER use the `preview` field in `AskUserQuestion`.** The preview renders ASCII art / mockups / code snippets in a fixed-width side box that gets aggressively truncated on narrow terminals — the user typically sees only one line plus an unhelpful "N lines hidden" footer. Once truncated, the content is unreachable without resizing the terminal, which defeats the entire point of the preview. The user has explicitly confirmed this fails on his setup.
- **Describe options through text fields instead.** Put the comparison into `label` (short choice name) + `description` (trade-offs, structure, implications in plain prose). For layout/structure differences, describe with words: "Two buttons side-by-side, equal width, fill the row" beats any ASCII mockup. For visual differences (alignment, spacing, density), use precise language: "stack vertically, full width", "centered, fixed 320px width", "iOS-style stacked buttons".
- **If a visual comparison genuinely cannot be conveyed in prose** (rare — usually means the user needs a screenshot/Figma link from me, not an ASCII drawing) — render the variants as code blocks or markdown in a regular chat message FIRST so they live in the scrollable conversation area, then call `AskUserQuestion` with text-only options that reference them ("Option 1 — full-width 50/50", "Option 2 — centered fixed"). Never stuff the visual artifact into `preview`.
- **Rationale.** Terminal width is unknown from the tool side; chat-pane text scales to whatever the user has, `preview` does not. When in doubt: text-only options, always.
