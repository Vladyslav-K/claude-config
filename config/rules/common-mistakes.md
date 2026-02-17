# Common Implementation Mistakes

Curated rules derived from real mistakes across projects.
Agents read this file before implementation to avoid repeating known issues.

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
