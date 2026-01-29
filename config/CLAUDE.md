**MEMORY SYSTEM ACTIVE:** Read `.claude/rules/memory-system.md` for project memory management. At session start, check if `.claude/memory/` exists and read its contents.

---

## Code Rules

- DON'T leave any comments what not connected to code, like tasks description, changes notes, etc.
- DON'T create any .md or other text files if you are not ordered to do it.
- DON'T create tests if you are not ordered to do it.
- With me, you ALWAYS speak on Ukrainian, but ALL generated code, comments, files must be only on English language, if not ordered other language.
- DON'T add yourself in commits, all commits must clear.
- ALWAYS check what package manager project using before run scripts!!!
- Before install any new library in project, ALWAYS check latest stable version with context7 or in Web!!!
- For reading and editing xlsx files use openpyxl.

---

## Post-Task Requirements

- AFTER FINISHED TASK ALWAYS RUN NEXT SCRIPT - format-and-check - AND FIX ISSUES IF FOUNDED!!!
- If this command don't exist, use next scripts - format, lint, typecheck.
- DON'T use custom commands with npx for this, we have this commands in package.json!!!

---

## CRITICAL: Task Execution Workflow

**YOU MUST FOLLOW THIS WORKFLOW FOR ALL CODING TASKS:**

### Step 1: Research Phase (DELEGATE to codebase-searcher)
- Read and understand the task or list of tasks from the user
- **Delegate research to `codebase-searcher` agent** for complex searches
- Use the Task tool with `subagent_type: "codebase-searcher"`
- The agent will find files, read code, and return the context you need
- Based on agent's findings, plan what needs to be done
- **Run multiple codebase-searcher agents in parallel** if you need to find different types of information

### When to Use codebase-searcher vs Direct Search
**USE codebase-searcher for:**
- Finding patterns across multiple files
- Understanding how similar features are implemented
- Gathering context for complex tasks
- Exploring unfamiliar parts of the codebase

**DO IT YOURSELF for:**
- Reading a single specific file path that user provided
- Very simple queries like "read package.json"
- Quick checks of 1-2 files you already know the path to

### Step 2: Implement Code (YOU do this)
- **Write code yourself** based on the research from codebase-searcher
- Follow existing patterns discovered during research
- Use the Edit/Write tools to create or modify files
- Ensure code follows project conventions and styles

### Step 3: Verify Results (YOU do this)
- After implementation, verify the changes match requirements
- Run typecheck, lint, and format commands (`format-and-check` or equivalent)
- If issues found - fix them yourself immediately

### Why This Workflow?
- `codebase-searcher` efficiently gathers context without consuming main session tokens
- You write code directly with full context from the conversation
- Quality verification happens in the main session where you have full control

### Example:
```
User: "Add a new button component"

You:
1. Delegate to codebase-searcher: "Find existing button patterns, UI components structure, design system conventions"
2. Receive context from codebase-searcher (full code examples, import paths, type definitions)
3. Write the code yourself using patterns from research
4. Run format-and-check and fix any issues
```

---

## codebase-searcher Agent Guidelines

**USE THIS AGENT FOR CODEBASE RESEARCH:**

### Primary Purpose
Gather CONCRETE code examples and patterns that you will use as reference when writing code.
The goal is collecting COPY-PASTE ready code snippets that show how this project does things.

### When to Use codebase-searcher
- Finding files by patterns or names
- Reading file contents across multiple files
- Searching for code patterns, types, interfaces
- Understanding existing implementations
- Finding dependencies and imports
- Exploring project structure
- Gathering context before implementing changes

### When NOT to Use (do it yourself)
- Reading a single specific file path that user provided directly
- Very simple queries like "read package.json"
- Quick checks of 1-2 files you already know the path to

### How to Use
```
Task tool with subagent_type: "codebase-searcher"
Prompt: Clear description of what you need to find/read
```

### Agent Capabilities
- Can: Read files, Glob search, Grep search, explore codebase
- Cannot: Write/edit files, use MCP tools, make changes

### CRITICAL: What to Ask codebase-searcher to Return

Always ask codebase-searcher to return SPECIFIC things you need:

**Your prompt to codebase-searcher MUST request:**
1. Full code of similar components (not summaries)
2. Exact import paths used in this project
3. Type/interface definitions that will be needed
4. Actual file paths (absolute paths)
5. Code style patterns observed (tabs/spaces, quotes, etc.)

**Example of GOOD codebase-searcher prompt:**
```
I need to create a new UserCard component. Find and return:

1. FULL CODE of 1-2 similar card components in this project (not summaries - actual code)
2. How Avatar component is used - show actual usage code
3. How Badge component is used - show actual usage code
4. User type/interface definition if exists
5. Import paths for Shadcn components used in this project
6. What directory pattern is used for components (e.g., /components/ui/ vs /components/)

Return actual code snippets I can use as reference.
```

**Example of BAD codebase-searcher prompt:**
```
Find card components in the project and tell me how they work.
```
(This will return descriptions instead of code)

### Running Multiple Searches in Parallel
When you need different types of information, run multiple codebase-searcher agents in parallel:
```
Agent 1: "Find card/list item components - return FULL CODE of 2 best examples"
Agent 2: "Find all Shadcn UI imports and how they're used - return actual import statements"
Agent 3: "Find User/Profile types - return full type definitions"
```

### After codebase-searcher Returns

Before writing code, verify you received:
- [ ] At least 2 full code examples (not descriptions)
- [ ] Actual import paths from this project
- [ ] Relevant type definitions
- [ ] Exact file paths

If codebase-searcher returned summaries instead of code - ask again more specifically.

---

## CRITICAL: Figma-to-Code Translation Rules

**When you have Figma JSON, screenshots, or design specs, you MUST follow these rules:**

### 1. NO APPROXIMATIONS - EVER
- NEVER use: "about", "approximately", "around", "roughly", "~"
- ALWAYS calculate exact values
- BAD: "Image should be about 70% width"
- GOOD: "Image: w-[990px] or w-[68.75%] (990/1440)"

### 2. MANDATORY Dimension Conversion
Before writing code, you MUST convert ALL Figma dimensions to exact Tailwind classes:

**For EVERY element extract and calculate:**
- Width: `w-[Xpx]` AND percentage `w-[X%]` (formula: element_width / container_width * 100)
- Height: `h-[Xpx]` or `min-h-[Xpx]`
- Padding: Convert `p:[top,right,bottom,left]` to `py-[top] px-[right]` or `p-[Xpx]`
- Gap: `gap-[Xpx]` or `gap-X` (divide by 4 for Tailwind scale)
- Border radius: `rounded-[Xpx]`
- Font size: `text-[Xpx]`
- Line height: `leading-[Xpx]`
- Letter spacing: `tracking-[Xpx]`
- Colors: Always exact hex `bg-[#XXXXXX]` or `text-[#XXXXXX]`

### 3. MANDATORY Dimension Table
When working with Figma specs, ALWAYS create this table before writing code:

```markdown
## DIMENSION SPECIFICATIONS (from Figma)
Container width: [X]px

| Element | Figma px | Tailwind Class | % Calculation |
|---------|----------|----------------|---------------|
| [name] | [X]px | w-[X]px or w-[Y%] | X/container*100 |
```

**Example:**
```markdown
## DIMENSION SPECIFICATIONS (from Figma)
Container width: 1440px

| Element | Figma px | Tailwind Class | % Calculation |
|---------|----------|----------------|---------------|
| Card width | 619px | w-[619px] or w-[43%] | 619/1440=0.43 |
| Card height | 703px | min-h-[703px] | - |
| Card padding | 64/32 | py-16 px-8 | 64/4=16, 32/4=8 |
| Image width | 990px | w-[990px] or w-[69%] | 990/1440=0.69 |
| Image height | 742px | h-[742px] | - |
| Title size | 48px | text-[48px] | - |
| Title line-height | 60px | leading-[60px] | - |
| Title letter-spacing | -3px | tracking-[-3px] | - |
| Body text | 22px | text-[22px] | - |
| Body line-height | 32px | leading-8 | 32/4=8 |
| Button width | 260px | w-[260px] | - |
| Button height | 60px | h-[60px] or h-15 | 60/4=15 |
| Button radius | 5px | rounded-[5px] | - |
| Gap | 48px | gap-12 | 48/4=12 |
```

### 4. Color Extraction
Always extract ALL colors from Figma tokens or design:
```markdown
## COLORS (from Figma)
| Token | Hex | Usage |
|-------|-----|-------|
| $c0 | #532456 | Card background |
| $c1 | #FFFFFF | Text, button bg |
| $c2 | #14181A | Button text |
```

### 5. Pre-Implementation Self-Check for Design Tasks
Before writing design implementation code, verify you have:
- [ ] Dimension table with ALL elements
- [ ] Every width has BOTH px and % values calculated
- [ ] Every color as exact hex code
- [ ] Every padding/gap converted to Tailwind
- [ ] Every font size, line-height, letter-spacing
- [ ] Position/layout strategy clearly defined
- [ ] Z-index values if overlapping elements

**If ANY dimension is missing exact values - calculate first, then write code.**

---

## Responsive Design Rules

**Figma typically shows only desktop (1440px). You MUST handle responsive:**

### Default Responsive Strategy
If user doesn't specify mobile behavior:
1. **Ask user**: "How should this look on mobile?"
2. **Or apply safe defaults**:
   - Side-by-side -> Stack vertically on mobile
   - Fixed widths -> Full width on mobile
   - Overlapping elements -> Stack on mobile
   - Large text -> Scale down proportionally

### Breakpoint Mapping
```
Mobile: < 768px (default, no prefix)
Tablet: md: (768px+)
Desktop: lg: (1024px+)
Large: xl: (1280px+)
```

### Responsive Dimension Table
When implementing, include responsive variants:
```markdown
| Element | Mobile | Tablet (md:) | Desktop (lg:) |
|---------|--------|--------------|---------------|
| Card | w-full | w-[619px] | w-[619px] |
| Image | w-full h-auto | w-[70%] | w-[990px] |
| Layout | flex-col | relative/absolute | same |
```

---

## Priority Hierarchy

**When information conflicts, follow this priority:**

### 1. User's Explicit Instruction (HIGHEST)
What user said in current chat > Everything else
```
User: "Make the button red"
-> Even if Figma shows blue button, make it red
```

### 2. Figma/Design Specs
Figma dimensions > Your assumptions
```
Figma: Card width 619px
-> Use 619px, don't round to 600px or 50%
```

### 3. Existing Codebase Patterns
How this project does things > General best practices
```
Project uses: import { Button } from '@/components/ui/button'
-> Use this, not: import Button from 'some-other-lib'
```

### 4. CLAUDE.md Rules
These rules > Default Claude behavior
```
Rule: "Use tabs for indentation"
-> Follow even if you prefer spaces
```

### 5. General Best Practices (LOWEST)
Only when nothing above applies

---

## Image and Asset Handling

**When Figma references images:**

### Before Implementing
1. **Check if image exists**: Look in `/public/images/` for the asset
2. **If exists**: Use exact path from project
3. **If not exists**:
   - Note: "Image needs to be exported from Figma"
   - Use placeholder or similar existing image
   - Add comment: `// TODO: Replace with actual image from Figma`

### Image Optimization
- Use Next.js `Image` component (not `<img>`)
- Provide width and height from Figma specs
- Use appropriate `alt` text

### Asset Export Request
If images are missing, tell user:
```
"The following images need to be exported from Figma:
- [image name] - [Figma node ID if available]
- [image name] - [dimensions needed]

Please export these to /public/images/[folder]/ and let me know when ready."
```
