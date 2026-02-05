# Figma-to-Code Translation Rules

**CRITICAL: When working with Figma JSON, screenshots, or design specs, you MUST follow these rules exactly.**

---

## 1. NO APPROXIMATIONS - EVER

- NEVER use: "about", "approximately", "around", "roughly", "~"
- ALWAYS calculate exact values
- BAD: "Image should be about 70% width"
- GOOD: "Image: w-[990px] or w-[68.75%] (990/1440)"

---

## 2. MANDATORY Dimension Conversion

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

---

## 3. MANDATORY Dimension Table

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

---

## 4. Color Extraction

Always extract ALL colors from Figma tokens or design:
```markdown
## COLORS (from Figma)
| Token | Hex | Usage |
|-------|-----|-------|
| $c0 | #532456 | Card background |
| $c1 | #FFFFFF | Text, button bg |
| $c2 | #14181A | Button text |
```

---

## 5. Pre-Implementation Self-Check

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

## 6. Responsive Design

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

## 7. Image and Asset Handling

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

---

## 8. Pre-Implementation Checklist

Before writing any design implementation code, ensure you have prepared:
- Full dimension table with calculated values
- Color table with exact hex codes
- Responsive breakpoint strategy
- Image paths or TODO placeholders
- Layout structure (flexbox/grid, positioning, z-index)

**Never start coding design tasks without exact specifications.**
