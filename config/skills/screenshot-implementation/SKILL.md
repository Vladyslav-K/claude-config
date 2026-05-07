---
name: screenshot-implementation
description: Visual fidelity protocol for implementing UI from screenshots, mockups, or design documents. Defines source-of-truth hierarchy (user instruction → *__design.md → screenshot → task description → existing code), mandatory phases (visual inventory top-to-bottom + left-to-right, component mapping by visual type, hard rules for text verbatim, element order, no extras, no omissions, self-review pass). Use when the task includes a screenshot, image, mockup, design document (*__design.md), or any visual UI specification to implement. Triggers on phrases "from this screenshot", "implement this design", "build this layout", "this mockup", "this page", attached PNG/JPG images, design docs in .project-meta/tasks/plan/screenshots/.
---

# Screenshot & Design-First Implementation

**Scope.** This skill applies whenever a task includes a screenshot, image mockup, or design document (`*__design.md`) to implement.

It complements the `component-craftsmanship` skill (judgement on how to build well) — this skill is the **fidelity layer** (don't deviate from what the design specifies).

---

## Source of Truth (in order of priority)

1. **User's explicit instruction** in current chat — overrides everything
2. **Design document** (`*__design.md`) — defines EVERY element: sizes, colors, text, spacing, states
3. **Screenshot** — visual verification of design interpretation
4. **Task description** — business requirements and scope
5. **Existing codebase** — component reference ONLY (how to import/use, not what to build)

---

## Hard Rules (apply before, during, and after coding)

- If it's not in the design — it DOES NOT exist. Don't build it.
- Existing pages are NOT templates. They show which components exist, not what your page looks like.
- For every element you build — point to the exact line in the design document.
- NEVER trust component defaults for visual styling. ALWAYS override with exact values from design via `className` or props.
- Extract exact hex values for colors, exact px for spacing, exact font specs from design.

**Key non-negotiables:**
- Analyze screenshot **top-to-bottom, left-to-right** — preserve this exact order in code
- Copy ALL text **verbatim, character by character** — NEVER rephrase, translate, or "improve"
- Match the **exact visual component type** (screenshot shows Switch → use Switch, not Checkbox)
- Search and read actual project components BEFORE coding — understand their API
- **If in design → MUST be in code. If NOT in design → MUST NOT be in code.**
- If unsure about ANY element — ASK, don't guess

Extract EVERY UI element from the design:
- Each section: elements, text, dimensions, colors
- Tables: EVERY column header, cell content format, row variations
- Interactive elements: type, states (hover/active/disabled)
- Badges/tags: text, colors, border-radius

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

---

## API Verification (CRITICAL)

When user provides screenshots/designs WITHOUT API docs:
- **STOP** before creating types, services, or hooks
- **ASK:** "Is there a backend API? What are the endpoints?"
- If no API → UI with mock data only
- **NEVER invent** endpoints, field names, or response structures from a screenshot
