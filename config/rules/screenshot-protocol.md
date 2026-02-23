# Screenshot Implementation Protocol

**When a task includes a screenshot to implement — follow this protocol STRICTLY.**

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
