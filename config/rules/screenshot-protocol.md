# Screenshot Implementation Protocol

**When a task involves implementing a design — in ANY format (screenshot, image, Figma file or export, design code from a designer, HTML/CSS handoff, exported asset, video / recording of a design, any other transfer of "what it should look like" from the user to me) — follow this protocol STRICTLY.** The file name says "screenshot" for historical reasons, but the scope covers every design-to-code transfer. If the user is giving me a visual contract for what to build, this file applies.

---

## Phase 0: Tempo & Mindset (read before doing ANYTHING else)

**Your goal in a design-implementation task is a pixel-perfect, word-for-word copy of the design — NOT "ship it fast".** The two outcomes are only compatible when you commit to slowness up front. Pick slowness. Always.

### Hard rules

- **Speed is NOT a goal here. Accuracy is the only goal.** If you catch yourself thinking "це достатньо близько", "приблизно так", "я зекономлю час якщо не звірятиму ось це", "ну це ж дрібниця" — STOP. The cost of one missed detail is always higher than the cost of one extra minute of inspection.
- **Every visible element must be inspected before code is written.** Not skimmed — inspected: text content character by character, colors as exact values (hex or design-token name), font family / weight / size / line-height / letter-spacing, padding and margin in concrete units, alignment, border, radius, shadow, gap, opacity. All of these, on every element. No "the user won't notice that one" assumptions.
- **Silent changes are FORBIDDEN.** You are not allowed to silently change anything: not text, not order, not component type, not color, not spacing, not size, not weight, not letter-case, not punctuation, not whitespace, not icon shape, not alignment. If something on the design looks wrong or you think you have a better idea — say so EXPLICITLY in chat and wait for the user's decision. NEVER improvise. NEVER "improve". NEVER "fix" the design.
- **Silent omissions are FORBIDDEN.** If you cannot understand what an element is or how to implement it — ASK. Do NOT skip "because it looks small" or "because I'm not sure what it is". Every visible element must end up in the code. Zero exceptions.
- **Silent additions are FORBIDDEN.** If you feel the design "needs" a divider, a hint, a help text, a tooltip, an extra button, an icon, a loading state that isn't shown — it does not. The design is the contract. Only what is on the design exists in code. Improvement suggestions go in chat, not in code.

### What "pixel-perfect" actually requires

For EVERY element you implement, extract and match all of these — never approximate, never guess:

- **Text:** verbatim — every character, capitalization, punctuation, whitespace, line break, ellipsis (`…` vs `...`), dash type (`—` vs `–` vs `-`), quote type (`« »` vs `" "` vs `" "`), apostrophe shape (`'` vs `'`), non-breaking space if present.
- **Color:** exact hex (or design-token name) — extracted from the design, not "приблизно синій". For gradients: each stop's color AND position AND opacity. For semi-transparent layers: exact percentage / alpha.
- **Font:** family, weight, size, line-height, letter-spacing — all five, explicitly. "Приблизно 16px" is not acceptable.
- **Spacing:** measured in concrete px (or design-token names from the project's scale). No "десь 16px" — read the actual value from the design tool. If the design shows decimals (e.g., 15.5px), round per the project's scale and ASK if unclear.
- **Sizes:** width, height, padding (all four sides explicitly if asymmetric), margin (all four sides), border-radius (each corner if asymmetric) — concrete values.
- **Borders & shadows:** for borders — width, color, style; for shadows — x-offset, y-offset, blur, spread, color, opacity, and inner vs outer. Every parameter explicit.
- **Order:** elements in the same sequence on screen as in the design, top-to-bottom and left-to-right. Sections, columns, rows, list items, navigation entries — same order.
- **Component variants:** match the visual type exactly (Switch vs Checkbox, Tab vs Link, Radio vs Select, Chip vs Badge vs Tag, Ghost button vs Outline button vs Text button, Card vs Tile, Modal vs Dialog vs Sheet vs Drawer).
- **Iconography:** the exact icon shape from the design, at the exact size, with the exact color and stroke weight. Do not "find something close" — confirm the project has the same icon, or ASK.
- **Density & alignment:** padding scale, line heights, vertical rhythm. The eye reads alignment before it reads content; misalignment shows up immediately.

### When the design is unclear — STOP and ask

You MUST stop and ask. Acceptable AND mandatory triggers for stopping:

- A text fragment is illegible, cut off, or pixelated in the screenshot
- A color cannot be confidently extracted (gradient with no token, anti-aliased edge, low-res image)
- An element is partially visible (cut by viewport, overlapped by another layer, behind a modal)
- An interactive state is not shown but the design assumes it exists (hover, focus, disabled, error, loading, empty)
- Two elements look almost identical but might be different components (is this a button or a chip? a switch or a checkbox?)
- A spacing value lies between two scale steps and the design doesn't disambiguate
- The design appears inconsistent with itself (the same component looks slightly different in two places — which is correct?)
- You see something that contradicts the project's design-system tokens (a color or size that does not exist in the system)
- The design contains text in a language you cannot read confidently — ASK for the exact characters

**Acceptable answer when unsure:** "Я не впевнений, що це — спитаю перед тим як писати." **Unacceptable answer:** writing something and hoping it's right. Hope is not a strategy here.

### The mindset rule

Treat every design-implementation task as if the user is going to compare every pixel against the original after you're done. Because that is exactly what they will do. Better to ask three times mid-task than to deliver something that requires a second review pass to fix.

"Pixel-perfect" is not a marketing phrase here — it is the contract. The job is **ідеальна копія дизайну**, not "зробити пошвидше". Those are different outcomes. Only the first one counts.

---

## Phase 1: Visual Inventory (MANDATORY before any code)

Analyze the screenshot **systematically, top-to-bottom, left-to-right**:

1. Divide the screenshot into visual zones/sections (header, content area, sidebar, footer, etc.)
2. For EACH element in EACH zone, record:
   - **Position**: where exactly it sits (top/middle/bottom, left/center/right)
   - **Element type**: heading, paragraph, button, input, select, radio, checkbox, table, card, badge, icon, tabs, etc.
   - **Exact text**: copy VERBATIM — every character, every word, as-is. Do NOT rephrase, translate, shorten, or "improve"
   - **Visual style**: approximate color, size, weight, variant (primary/secondary/ghost/outline)
   - **Order**: number each element sequentially as it appears top-to-bottom, left-to-right

**Output this inventory as a structured list before coding.**

---

## Phase 2: Component Mapping (MANDATORY before any code)

For EACH element from the inventory:

1. Determine the **visual type** first — what does it LOOK like? (dropdown = Select, round toggles = Switch, chips = Badge, etc.)
2. Search the project for a matching component (Glob/Grep by visual type name)
3. Read the found component's API — props, variants, slots, children format
4. Pick the component that **visually matches** the screenshot element
5. If no existing component matches → note that custom implementation is needed
6. If multiple components could match → ASK the user which one to use
7. If unsure about ANY element → ASK, don't guess

---

## Phase 3: Hard Rules

### Text
- **NEVER** change, rephrase, translate, abbreviate, or "improve" text visible on the screenshot
- Copy text **character by character** — including capitalization, punctuation, spacing
- If text is partially visible or unclear — ASK the user for the exact text

### Order
- **NEVER** reorder elements — code MUST match the visual top-to-bottom, left-to-right order
- Sections in code must appear in the same sequence as on the screenshot
- Columns in tables must follow left-to-right order from the screenshot
- Items in lists/grids must follow the screenshot order

### Components
- **NEVER** substitute a different component type than what the screenshot shows
- If the screenshot shows radio buttons — use radio buttons, NOT a select/dropdown
- If the screenshot shows tabs — use tabs, NOT a nav/links
- If the screenshot shows a toggle/switch — use a switch, NOT a checkbox
- Match the visual appearance: if it looks like a ghost button, use ghost variant, not default

### Content
- **NEVER** add elements, sections, columns, or features NOT visible on the screenshot
- **NEVER** omit elements that ARE visible on the screenshot
- Every visible element must have a corresponding piece of code
- If the screenshot shows 5 table columns — code must have exactly 5 columns, not 4, not 6

---

## Phase 4: Self-Review (MANDATORY after implementation)

Walk through the screenshot one more time, element by element:

1. Is every element from the screenshot present in the code?
2. Are elements in the exact same order?
3. Is all text exactly the same — character by character?
4. Are the correct component types used for each element?
5. Are there any extra elements in the code that don't exist on the screenshot?

If ANY answer is "no" — fix it before reporting completion.

---

## When to Show the Inventory to the User

- **Complex tasks** (new pages, multi-section layouts): ALWAYS show inventory + component mapping → wait for approval
- **Standard tasks** (adding a section, modifying existing layout): show a brief summary of what you see → proceed
- **Simple tasks** (changing text, swapping an icon): proceed directly, but still follow the hard rules

---

## Common Mistakes to Avoid

| Mistake | Example | Correct behavior |
|---------|---------|-----------------|
| Rephrasing text | Screenshot: "Додати новий" → Code: "Створити" | Use "Додати новий" exactly |
| Reordering columns | Screenshot: Name, Email, Role → Code: Role, Name, Email | Follow screenshot order |
| Wrong component | Screenshot shows Switch → Code uses Checkbox | Use Switch component |
| Adding extras | Screenshot has 3 buttons → Code has 4 buttons | Only 3 buttons |
| Omitting elements | Screenshot has a search input → Code skips it | Include the search input |
| Wrong variant | Screenshot shows outlined button → Code uses filled/default | Use outline variant |
