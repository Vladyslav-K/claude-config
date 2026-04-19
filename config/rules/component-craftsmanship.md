# Component Craftsmanship

**Scope.** This file applies whenever you create, edit, or fix UI components — regardless of framework. It works alongside `frontend-rules.md` (defaults: naming, syntax, stack) and `screenshot-protocol.md` (fidelity to screenshots). This file is the **judgement layer**: what to read first, when to reuse vs build, how to make the result objectively good, when to stay literal vs propose alternatives.

**Why this exists.** Without explicit triggers, components get built badly: equal-percent layouts that ignore hierarchy, raw `<button>` with custom utility classes when a project Button exists, copy-paste from another page instead of reuse, primary actions in mobile top-left where no thumb reaches. Each failure has the same root cause — skipping the analysis step. The triggers below force the analysis.

---

## 0. Project-First Principle

Every rule below is a **default that applies only when the project has no established convention of its own**. If the project already does it differently — follow the project. The job is to match the codebase, not push these defaults onto it.

Check before applying any default below:
- Does the existing code use a different pattern? → follow the existing pattern
- Does the design system / linter / theme config disagree? → follow the project config
- Is the project a different paradigm (vanilla CSS, BEM, CSS-in-JS, utility-first, atomic CSS, etc.)? → match what is there
- Is the framework different from your default (Vue, Angular, Svelte, Solid, vanilla, older React)? → ignore framework-specific shapes in this file, keep the principles

---

## 1. Pre-flight (mandatory before ANY UI code)

Before writing or editing component code, complete these reads. Skipping any of them is a guess — and guesses produce the failures listed in section 7.

**Required reads:**

1. **Component library inventory.** Glob the project for `components/`, `ui/`, `shared/components/`, `packages/ui`, `lib/components`, or equivalent. List what exists. If nothing found — say so explicitly before proceeding.
2. **2–3 sibling components.** Read components similar to what you are about to build. Learn the project's API conventions: prop names, variants, composition patterns, slot/children format, how styling is overridden.
3. **Theme / tokens file.** Find and read the project's design tokens: spacing scale, color palette, type scale, radii, shadows. Common locations: `theme.ts`, `tokens.ts`, `tailwind.config.*`, `_variables.scss`, `design-tokens.json`, `styles/variables.css`. If you cannot find one — ask before inventing values.
4. **The file you are editing (if editing).** Read the entire file, not just the lines mentioned in the request. The surrounding code holds the context that explains why the current code looks the way it does.
5. **Closest neighboring page or screen.** Open one similar page in the same project. This is the project's design language — match it.

**Output of pre-flight.** Before the first edit, name (in your response) the components found, the spacing scale values, and the closest sibling page. This proves the reads happened. If you cannot name them — you have not done the pre-flight.

**Failure mode this prevents.** Building a `<Card>` from scratch when the project already has one. Inventing a `padding: 13px` when the project's scale is 4/8/16/24. Picking a color that does not exist in the palette. Re-implementing a Button with utility classes because you did not look.

---

## 2. Reuse Hierarchy (use this exact order, never skip)

**Hard rule first: raw HTML/template elements with custom styling do NOT belong in page/feature/route code, ever.** All UI primitives and compositions live in `components/` (or the project's equivalent — `ui/`, `shared/components/`, `packages/ui`, `lib/components`). Page code consumes those components; it never inlines raw `<button>`, `<input>`, `<div class="card-like">`, etc. with bespoke styling. This is true even when the matching component does not exist yet — in that case you create the component first, then use it from page code.

Walk this order whenever you need a UI primitive or composition:

1. **Existing project component matches as-is.** Search by visual type — button, icon button, input, card, modal, table, badge, tabs, dropdown, switch, etc. Use it. Override styling only via its documented props/variants/className-passthrough, not by wrapping with custom classes that fight its internals.
2. **Existing component, but a stylistic variation is needed** (different size, color, weight, shape, padding scale, density, etc.). **Extend the existing component** by adding a new variant or prop. Do not inline the variation in page code. Decision rule: extend (new variant/prop) when the variation is a natural relative of the existing component; create a new related component when extending would distort or bloat the original. **If unsure which path — ASK before writing code.**
3. **Composition of existing primitives.** When the new shape is a combination of 2–3 existing components (e.g., a card composed of `<Card>`, `<Avatar>`, `<Button>`), compose them. The composition can live inline if used once and is genuinely page-specific; extract it to `components/` if the composition recurs or feels like its own concept.
4. **No existing component fits and extension would distort it.** Create a new component in `components/`. Even if it is used only once today. Page code then imports and uses it. Add a one-line code comment describing what it is and when to reach for it.

**Anti-pattern: copy-paste from another page.** If you find yourself copying markup from another file into the new one — STOP. Two cases:
- **Source has the pattern as a proper component** → import the same component in the new location, do not copy markup.
- **Source has the pattern as raw inline elements** → do NOT carry the raw forward. Extract the pattern to `components/` first, refactor the source page to use the new component, then use the new component in your new place too. The copy-paste is your signal that the original location was wrong and needs fixing alongside.

Even if the user explicitly says "copy this card from page X" — if X has the card as raw inline markup, the correct execution is "I will extract this to a component in `components/`, refactor page X to use it, then use it in the new page too". Not "I copy-paste the raw markup". Surface this in your response if the user request implies the wrong path; do not silently propagate the original mistake.

**Anti-pattern: raw element with custom styling in page code.**

Wrong (in any page/feature/route file):
```
<button class="px-4 py-2 bg-blue-500 rounded text-white hover:bg-blue-600">Save</button>
```

Right (in page/feature/route file):
```
<Button variant="primary">Save</Button>
```

If `Button` does not exist, or it exists but lacks the needed variant — go create or extend it in `components/` first, then use it from page code. The fix is never "inline custom styles in the page".

The principle holds in any framework — React, Vue, Svelte, Angular, vanilla. It applies to **all** components, not just buttons: inputs, cards, modals, badges, switches, dropdowns, icon buttons, list rows, etc. Components in `components/` ship with states, accessibility, theming, dark mode, translation hooks, telemetry, and a single source of truth. Inline raw elements in page code ship without them and fragment the UI vocabulary every time someone writes one.

**When in doubt: ASK.** Specifically — when you cannot decide whether to (a) use an existing component as-is, (b) extend an existing component with a new variant/prop, (c) compose existing primitives, or (d) create a new component — describe the choice to the user and ask which path before writing code. Asking is always preferred over guessing.

---

## 3. Quality Triggers — Operationalized "Good"

"Good" is not a feeling. It is the conjunction of objective checks below. Every component must pass all five blocks.

### 3.1 Hierarchy

- **One primary element per section.** Identify it before styling anything. Make it the visual focus through size, weight, or color.
- **Secondary elements step down.** Smaller, lighter, or muted relative to primary.
- **Tertiary (metadata, icons, captions) step down again.** Smallest, most muted.
- **Scan-path question.** What does the eye land on first? Is that what the user needs to see first? If no — re-rank.

**Counter-example: equal allocation for unequal elements.** A card with title + body + icon split 33/33/33 is broken because those three are not equal in importance. Title is primary, body is secondary, icon is anchoring tertiary. Layout must reflect that — usually a column with title at the top, body below, and the icon as a small accent inline with title or floating top-corner.

### 3.2 Density / Spacing

- **Use the project's spacing scale only.** Common scales: 4/8/16/24/32/40/48 (8pt grid) or 4/8/12/16/20/24 (4pt grid). Read the project's tokens to find the actual scale. Never invent values like `padding: 13px` or `margin: 22px`.
- **Internal padding ≤ external margin.** Items inside a card breathe less than the spacing between cards. Inverting this breaks visual grouping.
- **Whitespace is content.** Empty space lets the eye rest and groups related elements. Do not fill empty space just because it is there.
- **Adjacent elements need clear separation.** Text must not touch borders, icons, or other text. Minimum 8px between adjacent tappable elements on touch.

**Counter-example.** Picking arbitrary px values defeats the rhythm the project's scale creates. The eye perceives proportional repetition as orderly; arbitrary values look noisy even when no individual one is "wrong".

### 3.3 Layout & Composition

- **Match space allocation to importance.** A 50/50 split is correct only when the two halves are equally important. A 70/30 or 80/20 reflects unequal importance. Equal % for unequal elements destroys hierarchy.
- **Default direction for title + body + icon:** column with icon as accent (small, top-aligned or inline with title), title as the size anchor, body as the readable line below. Not three equal columns.
- **Alignment is invisible when right, loud when wrong.** Pick a single alignment per section (left for body text in LTR locales, sometimes center for short labels). Do not mix alignments inside one section.
- **Group by proximity.** Related elements close together; unrelated elements separated by larger gaps. The user reads grouping before they read content.

**Counter-example: fixing one element when the layout is wrong.** Shrinking the icon in a 33/33/33 card papers over the real issue — the layout itself. See section 4 for how to handle this without doing an unrequested redesign.

### 3.4 States

Every interactive element must have a complete state matrix. Missing states are the most common visual bug.

**Mandatory states (all that apply to the element type):**
- `default` — the resting state
- `hover` — pointer over (desktop)
- `focus-visible` — keyboard focus ring (a11y, never remove)
- `active` / `pressed` — during click/tap
- `disabled` — visually distinct, not interactive
- `loading` — when an async action is in progress (spinner, skeleton, or progress)
- `error` — when validation or operation fails (color + icon + message)
- `empty` — when a list/table/card has no data (illustration or text + a next action)

**Transition timing.** 100–300ms for state changes. Slower feels laggy, faster feels jarring.

**Focus rings are non-negotiable.** Removing the focus outline breaks keyboard navigation for everyone who uses it. Restyle (color, offset, width) to match the design — do not remove.

**Counter-example: only `:hover` styled.** Shipping a button with only hover state means keyboard users cannot see focus, async actions show no feedback, and disabled buttons look identical to enabled ones.

### 3.5 Mobile / Reach

- **Thumb zone matters.** ~49% of users hold their phone one-handed. The bottom of the screen is the green zone (easy reach), the right side is the next-best zone (right-handed default), the top corners are the red zone (avoid for primary actions).
- **Primary actions go bottom or right.** Save, Submit, Confirm, Continue, Pay — never in the top-left on a mobile layout.
- **Touch targets ≥ 44×44px** (iOS HIG) or ≥ 48×48px (Material). Smaller targets are misclick traps.
- **Spacing between adjacent tappable elements ≥ 8px.** Prevents accidental taps.
- **Test the mobile breakpoint, not just desktop.** A layout that works at 1440px often breaks at 375px. If the project has mobile-first conventions, follow them. If not, design mobile-first by default for new screens.

**Counter-example: Save button in mobile header-left.** This forces the user to either two-hand the phone or stretch their thumb across the screen on every interaction. It is wrong by default; only correct if the project explicitly establishes header-left as a primary-action slot.

---

## 4. Scope Calibration — Match the Request, Don't Inflate It

The most common failure is doing too much or too little relative to what was asked. Both are wrong. Use this decision tree.

### 4.1 Point-fix request

**Examples.** "Make the icon smaller", "change this color to red", "fix the padding here", "remove this element".

**Action:**
1. Make exactly the requested change. Nothing else in the same edit.
2. **Then scan one zoom-level out** — re-read the parent component or section. Does the surrounding context still work? Or did the request only ask you to mask a deeper problem?
3. If you spot a systemic issue: **surface it explicitly in your response, do not fix it.**

**Example response when systemic issue spotted:**
> "I made the icon smaller as requested. Note: the underlying issue is that the card uses a 33/33/33 split between title/body/icon, which will not scan well regardless of icon size — the icon is taking visual weight that belongs to the title. Want me to restructure the card to a column layout with the icon as a small accent? I will not do this without confirmation."

4. Wait for the user's answer before any restructuring.

**Anti-pattern.** Doing the literal fix and a "creative" redesign at the same time. The user asked for one thing; deliver one thing; surface the rest.

### 4.2 Scoped work

**Examples.** "Build this section", "add a settings panel here", "redo this card".

**Action:**
1. Read the whole screen first, not just the section in scope.
2. Apply all five quality triggers (hierarchy, density, layout, states, mobile).
3. Stay within the named scope. Do not edit other sections without asking.

### 4.3 Open-ended

**Examples.** "Build a new page for X", "make this look nice", "design a profile screen".

**Action:**
1. Full creative engagement — quality triggers are mandatory, not optional.
2. **Propose 1–2 layout options briefly before coding.** Sketch the structure in text (sections + which existing components per section). Wait for the user to pick one.
3. Then implement, applying all quality triggers.

---

## 5. Creativity Calibration — When to Propose Alternatives

Creativity is judgement, not unsolicited replacement. Use this table.

| Situation | Action |
|---|---|
| Tight literal request ("change color to red") | Just do it. No alternatives. |
| Vague request ("make a card for X") | Propose 1–2 options briefly, ask which to use. |
| You see a better path on a tight request | Mention it briefly in your response, do not act on it. |
| You see a systemic issue while doing point-fix | Surface it in response, ask before acting (see section 4.1). |
| Open-ended new build | Bring full creativity, propose layouts before coding (see section 4.3). |

**Hard rule: never replace a literal request with your alternative.** Add your suggestion on top, do not substitute. The user asked for X; deliver X; suggest Y separately if relevant.

**Hard rule: never silently expand scope.** If the request is "fix the icon" and you also redesigned the layout — that is a violation, even if the redesign is better. Surface, ask, then act.

**Hard rule: when stuck or unsure, ask.** "Which of these two layouts do you want?" beats picking one and being wrong.

---

## 6. Self-Review Checklist (after every UI task)

Before reporting the task as done, walk through every item below. If any answer is "no" or "I did not check" — go back and fix it before reporting.

1. **Pre-flight reads.** Did I read the component library, sibling components, and tokens file? Can I name them in my response?
2. **Reuse.** For each new component or markup, did I check the project for an existing equivalent? Can I name what I checked?
3. **Spacing scale.** Are all my spacing values from the project's scale? List the values used.
4. **Hierarchy.** Is there a clear primary element per section? Does it scan in 2 seconds?
5. **States.** Does every interactive element have all required states (default, hover, focus-visible, active, disabled, plus loading/error/empty where applicable)?
6. **Mobile.** Are primary actions in the thumb-friendly zone (bottom or right)? Are touch targets ≥ 44px? Is there enough spacing between them?
7. **Scope.** Did I do exactly what was asked, no more no less? If I noticed a broader issue — did I surface it without fixing it?
8. **Reused vs raw.** Are there any raw elements with custom styling left in page/feature code? If yes — extract them to `components/` (create the component first if it does not exist).
9. **Extend vs new.** If I needed a stylistic variation of an existing component, did I extend it (new variant/prop) or create a new related component in `components/`? If I had any doubt about which path — did I ASK the user first?
10. **Copy-paste check.** Did I copy any markup from another page into this work? If yes — did I extract it to a shared component (and refactor the source) instead of carrying it forward?

---

## 7. Common Failures (with corrections)

| # | Failure | Wrong | Right |
|---|---|---|---|
| 1 | Equal-percent split for unequal elements | 33/33/33 title / body / icon in a card | Column layout: title (primary), body (secondary), icon as small accent inline with title |
| 2 | Raw element with custom styling in page code | `<button class="px-4 py-2 bg-blue-500 rounded">Save</button>` directly in a feature/route file | `<Button variant="primary">Save</Button>`. If `Button` or the needed variant does not exist — create/extend it in `components/` first, then use it |
| 3 | Copy-paste raw markup from another page | Copying a 50-line block of inline raw elements from page A to page B as-is | Extract the pattern to `components/`, refactor page A to use it, then use the new component in page B too. Do not propagate the original raw mistake |
| 4 | Primary action in mobile top-left | Save button placed in header-left on mobile | Bottom of screen or right side (thumb-friendly zone) |
| 5 | Touch target too small | `<button>` wrapping a 24×24 icon with no extra hit area | Wrapper sized ≥ 44×44 around the icon |
| 6 | Missing states | Only `:hover` styled; no focus, no disabled, no loading | Full state matrix from section 3.4 |
| 7 | Inventing spacing values | `padding: 13px; margin-top: 22px;` | Use project scale (4/8/16/24...); read tokens file |
| 8 | Local fix masks systemic issue | Shrinking icon to 16px to "fix" a broken 33/33/33 card layout | Make the literal fix, surface the layout issue separately, ask before redesigning |
| 9 | Silent scope expansion | Asked to fix icon size, also rewrote the card layout in the same edit | Fix the icon as asked, surface broader issue, wait for go-ahead |
| 10 | Removing focus outline | `outline: none;` with no replacement | Restyle the focus ring (color, offset, width), never remove it |
| 11 | Mixing alignments inside one section | Left-aligned heading, center-aligned subhead, right-aligned body | One alignment per section |
| 12 | Touching borders / no breathing room | Text/icons touching the card edge or each other | Internal padding from project scale; whitespace as content |
| 13 | Inventing colors not in palette | Random hex like `#3b82f6` when the project palette uses `theme.colors.primary` | Use only palette values; if you need a new color, ask whether to extend the palette |
| 14 | Overriding component internals via specificity | `.MyButton button { padding: 5px !important; }` | Use the component's prop API or className-passthrough as designed |
| 15 | Inconsistent icon usage | Mixing icon sizes / styles / weights within one screen | One icon library, one size scale, consistent stroke/fill |
| 16 | Stylistic variation inlined in page instead of as a variant | `<Button style={{ background: 'red' }}>Delete</Button>` because no destructive variant exists | Add a new variant/prop to the component (`variant="destructive"`). If extending would distort the component, create a related component in `components/`. ASK if unsure which |
| 17 | Picked extend-vs-create-new on your own when unclear | Silently invented `<DangerButton>` instead of considering `<Button variant="danger">` (or vice versa) | When unsure between extending an existing component vs creating a new related one — ASK the user before writing code |
| 18 | Created a one-off UI piece inline in page code | "It is only used once, no need for a component" — wrote markup directly in the page | Even one-off UI primitives live in `components/`. Page code consumes; it never defines raw UI. Add a code comment naming when to reach for it |

---

## 8. When to Read This File

This file auto-loads at every session start (it lives in `.claude/rules/`). When the current task involves any UI code — new component, edit, fix, redesign, screenshot implementation, page build — apply it.

Entry point: section 1 (Pre-flight). Exit gate: section 6 (Self-Review). Skipping either makes the work a guess.
