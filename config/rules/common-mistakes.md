# Common Implementation Mistakes

Curated rules derived from real mistakes across projects.
Agents read this file before implementation to avoid repeating known issues.

## Page Structure

### Never add structural UI elements not present in the design
Before implementing tabs, modals, drawers, accordions, multi-step wizards, or any
structural page division — verify the design ACTUALLY shows these elements. Never
"borrow" structural patterns from similar/reference pages when the target design
shows a different structure (e.g., single continuous page vs tabbed layout).
The screenshot is the source of truth for page structure, not the reference code.
- Example: Detail page implemented with two tabs ("Request Details" + "Quotes") but design showed a single continuous page with both sections stacked vertically — no tab UI visible anywhere
- Example: Planner assumed tabs because reference page (users detail) used AnimatedTabs, but actual design screenshot had no tab controls at all

### Planner must verify every structural element against the screenshot
When writing task context during planning (tasks:plan), every major structural element
mentioned (tabs, modals, sections, accordions, multi-step flows) must be visually
confirmed in the screenshot. If the screenshot doesn't show tab controls, DON'T
write "TABS" in the task context — even if the reference page uses tabs.
- Example: Task context specified "TABS — Request Details | Quotes (0)" with full code, but screenshot showed continuous page — planner copied tab pattern from reference page without checking the design

### Full-width layout elements must be explicitly configured
When the design shows tabs, dividers, or navigation spanning the full content width,
the implementation must use the correct component props/CSS to achieve full-width
rendering. Don't assume components render full-width by default — check the component
API for fullWidth/stretch/grow props and verify the rendered result matches the design.
- Example: Tab bar should span full page width per design but rendered centered/auto-width because component wasn't configured for full-width mode

## Layout & Nesting

### Elements visually inside a container must be DOM children
When an element appears visually inside a container on the design
(shared background, within bounds), it MUST be a child of that container
in JSX, not a sibling placed after it.
- Example: "Sign Up" button inside header was coded as sibling after header

### Visually grouped elements need a shared wrapper
When elements share a common border, background, or shadow on the design,
they must be wrapped in a single parent container in code.
- Example: Table and pagination shared a border but were coded as separate sibling divs

## Colors

### Never approximate colors
Always extract exact hex values from Figma JSON or design analysis.
If working from screenshot only, match as precisely as possible and flag uncertainty.
- Example: Used #333 for text instead of exact #14181A from design

## Typography

### Always verify font-weight for every text element
Bold text on the design means explicit font-weight (600/700), not default.
Check every heading, label, and emphasized text.
- Example: Heading was semibold in design but coded with default (normal) weight

## Spacing

### Use exact spacing values from design specs
Never approximate padding, margin, or gap values. Extract exact values from
Figma JSON or design analysis.
- Example: Card had p-4 (16px) instead of correct py-8 px-6 (32px/24px)

## Text Content

### Every visible text must exist in code with exact content
After implementation, verify that every text string visible on the screenshot
exists in the code with the exact same wording.
- Example: Button label was "Submit" in code but "Save Changes" in design

## API & Data

### NEVER hallucinate API endpoints, types, or response structures
If the user provides only screenshots/designs without API documentation:
1. ASK the user if a backend API exists for this feature
2. ASK for endpoint paths, request/response shapes, field names
3. If no API exists or user hasn't confirmed, mark API tasks as BLOCKED
4. NEVER invent endpoint URLs, field names, or response structures based on UI
- Example: Created entire API layer (types, service, hooks) with fabricated endpoints `/api/admin/sourcing-requests` and invented field names that didn't match the real backend
- Example: Assumed `requestId` field exists when the actual API returned a different field name, resulting in empty columns

### Verify data fields against actual API before building UI
If you don't know the real field names from the API:
1. Ask the user to provide a sample API response or API docs
2. Or ask the user which fields are available
3. NEVER map UI columns to assumed/invented field names
- Example: Table had "Request ID" column mapped to `request.requestId` which was undefined in actual data

## Figma JSON Processing

### ALWAYS extract border specs from Figma JSON
When Figma JSON has `bd` (border) property on an element, you MUST add
the corresponding border in code. Check EVERY image, card, and container.
- Example: Product images had `bd: { w: 1, c: "$c13", style: "solid" }` in Figma but were coded without any border

### ALWAYS extract shadow/gradient specs from Figma JSON
Buttons and cards often have inner shadows (`inset` in `sh` property) that create
gradient effects. These are NOT optional decorations — they are core visual identity.
- Example: "Create Quote" button had `sh: "inset 0px 8px 20px -8px rgba(255,255,255,0.80)"` for gradient effect but was coded as flat purple

### Extract exact dimensions for ALL illustration/decorative elements
Empty states, icons, illustrations — always get exact sizes from Figma JSON.
Never use arbitrary values like 64x64 without checking the design.
- Example: "No Quote Yet" illustration was coded as 64x64 but Figma specified much larger dimensions

## Buttons & Interactive Elements

### Always extract full button styling from Figma
For every button, check Figma JSON for ALL of:
- Background color or gradient
- Inner shadows (inset) for gradient effects
- Border radius
- Icon presence and position (left/right)
- Exact padding values
- Text color and weight
- Example: "+ Quote" button was missing the "+" icon entirely
- Example: "Create Quote" button had gradient via inner shadow but was coded as flat color

## Images & Media

### Always check for borders on images
Product thumbnails, avatars, card images — check `bd` (border) property
in Figma JSON. Images frequently have subtle borders that are easy to miss.
- Example: Product images in table (40x40) and detail card (120x120) both had 1px solid border in Figma but were rendered without any border

## Visual Task Workflow

### NEVER skip analyzer agent for visual tasks
For ANY task with screenshots/Figma specs, the orchestrator MUST:
1. Spawn analyzer agent FIRST to read screenshot + Figma JSON
2. Analyzer produces element-by-element analysis with exact specs
3. Only THEN spawn implementer with analyzer's full output
Skipping analyzer = guaranteed design mismatches.
- Example: Tabs component was terribly wrong because no analyzer extracted exact tab styling from Figma JSON

### NEVER skip validator agent for visual tasks
After implementer finishes visual task, the orchestrator MUST:
1. Spawn validator agent with FRESH eyes (hasn't seen implementation)
2. Validator reads screenshot + implemented code
3. Validator reports EVERY discrepancy element by element
4. Orchestrator fixes all issues before marking done
Skipping validator = shipping broken visual implementations.
- Example: Multiple critical mismatches (wrong buttons, missing borders, wrong tabs, empty data columns) all passed "validation" because no validator agent was used

### Search codebase for existing patterns before implementing UI elements
Before implementing any visual element, research if the project already has:
- Country flags / flag components
- Status badges with specific variants
- Button variants (gradient, outline, etc.)
- Table patterns with specific column types
- Example: Destination column was empty because existing country flag solution in the project wasn't found and reused

## Tabs & Navigation Components

### Tabs must match exact Figma styling
Never use default/generic tab styling when Figma specifies custom styles.
Extract: active tab indicator, background color, text color, hover state,
close/action icons, border-bottom style.
- Example: Tabs were coded with generic Shadcn styling instead of matching Figma design (specific purple underline, background, close icon)

## Page Integration

### New pages MUST integrate with existing layout systems
When creating a new page/route, ALWAYS research and update:
1. Page title mapping (header component or metadata)
2. Sidebar navigation (if page should appear in menu)
3. Routing configuration (breadcrumbs, back buttons)
If you skip this, the page will show default fallback titles like "Page".
- Example: Sourcing Requests pages showed "Page" as title because route wasn't added to pageTitles mapping in header.tsx

### New pages must follow existing page structure patterns
Before creating a new page, find the most similar existing page and replicate
its structure: how it sets titles, how it handles layout, how it integrates
with navigation. Don't reinvent patterns that already exist.
- Example: Existing admin pages all used pageTitles mapping but new pages ignored this entirely

## Element Duplication

### Never duplicate action buttons on the same page
Count action buttons on the design screenshot. Count them in your code.
The numbers MUST match. Same-purpose buttons appearing in multiple sections
is almost always a mistake.
- Example: Detail page had Quote button in header row AND next to "Request Details" heading — design only showed ONE

### Count elements before and after implementation
For every element type (buttons, icons, badges, links), explicitly count:
- How many on the screenshot?
- How many in the code?
If code has MORE than screenshot → remove extras. If FEWER → add missing ones.
- Example: 3 Quote buttons in code when design showed 1 in header + 1 in empty state

## Role-Inappropriate UI

### Only add UI elements appropriate for the user role
Admin pages should NOT have user-specific elements unless explicitly shown.
User pages should NOT have admin-specific controls. Check:
- Notification bells → usually only for regular users, not admin
- User avatars/profiles → context-dependent
- Action buttons → only if design shows them for this role
- Example: Admin sourcing request detail page had notification bell with badge "3" but admin role doesn't have notifications feature

## Functional Completeness

### Interactive UI elements MUST be functional
If the design shows a filter dropdown, search input, or action button,
it MUST work — at minimum with mock data. Static buttons that look
interactive but do nothing are worse than missing elements.
- Example: 4 filter dropdowns (User Types, Date Range, Status, Has Sample) were rendered as static buttons with no state, no dropdown, no filtering logic

### Email addresses must be mailto links
When displaying email addresses in UI, they MUST be rendered as
`<a href="mailto:email@example.com">` clickable links, not plain text.
If the design shows email in a different color or with underline, it's a link.
- Example: User email in sourcing requests table was plain `<span>` text instead of clickable mailto link

### Phone numbers must be tel links
Similar to emails, phone numbers should be `<a href="tel:+1234567890">` links.

## Component Reuse

### Never recreate UI components that already exist in the project
Before implementing any UI element, check if the project already has a component for it.
Using raw `<button>`, `<input>`, `<select>` when project components exist is always wrong.
The Researcher's "UI Component Catalog" section lists what exists — use it.
- Example: Custom filter dropdowns were built from scratch with raw HTML while the project had
  `src/components/ui/custom-select.tsx`, `src/components/ui/input.tsx`, and existing admin filter
  patterns in `src/components/admin/users/user-filters.tsx`
- Example: A new Button component was created inline when `src/components/ui/button/button.tsx`
  already existed with all needed variants (primary, outline, ghost, gradient)

### Validator must grep for raw HTML primitives in new code
When validating, search all new/modified files for raw `<button`, `<input`, `<select` tags.
Each occurrence must be justified — either no component exists, or it's inside a component definition.
If a UI component for it exists in the project → CRITICAL ISSUE.

## Responsive Design

### Every visual page MUST have mobile/responsive layout
Any page or component created from a visual task (screenshot/Figma) MUST implement
responsive design. Absence of Tailwind responsive classes (`sm:`, `md:`, `lg:`) in new
page files is always a critical bug — not an oversight to ignore.
- Example: Full Sourcing Requests list page was implemented with desktop-only layout.
  Zero responsive classes existed — mobile users would see completely broken layout.
- Example: Filter bar with 4 dropdowns rendered as a single horizontal row on mobile
  with no wrapping or stacking behavior.

### Mobile-first implementation approach
Write default (unprefixed) Tailwind classes for mobile layout first, then override with
`md:` and `lg:` for larger screens. Key patterns:
- Tables: wrap in `overflow-x-auto` for mobile horizontal scroll
- Multi-column filter rows: `flex flex-wrap` or `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
- Sidebar/header: already handled by layout — focus on page content area
- Cards/grids: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
