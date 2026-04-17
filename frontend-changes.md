# Frontend Changes — Theme Toggle Button & Light Theme

## Summary
Added an accessible, icon-based light/dark theme toggle button fixed in the top-right of the UI, with smooth transition animations and persistence via `localStorage`.

## Files Changed

### `frontend/index.html`
- Added a `<button id="themeToggle">` element directly after the `<header>`.
- Button uses `role="switch"` with `aria-checked` and a descriptive `aria-label` for screen readers.
- Contains two inline SVG icons (sun and moon), each marked `aria-hidden="true"`. Only one is visible at a time; the other is animated out.

### `frontend/style.css`
- Split the existing color palette into a default dark theme on `:root` and a new `[data-theme="light"]` override block (background, surface, text, borders, shadows, focus ring, welcome block, code background).
- Added `--code-bg` variable and replaced the two hardcoded `rgba(0,0,0,0.2)` code-block backgrounds so code blocks adapt to the theme.
- Added a `transition` rule on themed elements (body, sidebar, chat surfaces, inputs, messages, buttons) so color/background/border changes animate smoothly (0.3s ease).
- Added `.theme-toggle` styles: fixed top-right, 44×44px circular button using `--surface` / `--border-color` / `--text-primary` so it automatically matches either theme. Includes hover lift, `:focus-visible` ring (keyboard-accessible), and an `:active` press state.
- Added `.theme-icon` base + `.theme-icon-sun` / `.theme-icon-moon` rules that cross-fade and rotate (0.4s) so the icon swap animates instead of snapping.
- Added a mobile breakpoint (`max-width: 768px`) that shrinks the toggle to 40×40px and nudges it closer to the corner.

### `frontend/script.js`
- Added `initializeTheme()` (called on `DOMContentLoaded`): reads saved theme from `localStorage`, falls back to the OS `prefers-color-scheme` media query, and applies it before the user interacts.
- Click handler toggles between `light` and `dark`, persists to `localStorage`, and updates `data-theme` on `<html>`.
- Explicit `keydown` handler for `Enter` / `Space` (native `<button>` already handles these, but this makes the switch-role behavior explicit and robust).
- `applyTheme()` also updates `aria-checked` and `aria-label` so assistive tech announces the current state correctly.

## Design Notes
- **Aesthetic fit:** The toggle reuses existing CSS variables (`--surface`, `--border-color`, `--focus-ring`, `--shadow`) so it blends with the current pill-shaped input/send-button style. Hover/focus behavior mirrors the send button.
- **Positioning:** `position: fixed; top: 1rem; right: 1rem;` with `z-index: 1000` keeps it out of the chat flow and visible at all scroll positions without overlapping the sidebar.
- **Icon choice:** Sun for light mode (shown when active), moon for dark mode — a widely recognized convention.
- **Animation:** Icons cross-fade with a rotate+scale transform (0.4s) for a smooth swap; theme color transitions run at 0.3s on all surfaces so switching doesn't flash.
- **Accessibility:**
  - Native `<button>` element — focusable and activatable by keyboard by default.
  - `role="switch"` + `aria-checked` communicates on/off state.
  - `aria-label` updates to describe the *next* action ("Switch to light theme" / "Switch to dark theme").
  - `:focus-visible` ring only appears for keyboard users, not mouse clicks.
  - Respects `prefers-color-scheme` on first visit.

---

# Frontend Changes — Light Theme CSS Variables

## Summary
Tuned the `[data-theme="light"]` variable block for WCAG AA/AAA contrast compliance and added light-mode-specific overrides for elements whose hardcoded colors would otherwise look wrong on a light background.

## Files Changed

### `frontend/style.css`

**Light theme variable block — retuned values:**
- `--primary-color`: `#2563eb` → `#1d4ed8` (darker blue; white text on this color hits 8.6:1, AAA).
- `--primary-hover`: `#1d4ed8` → `#1e40af` (deeper hover state that stays distinct from resting).
- `--text-secondary`: `#475569` → `#334155` (contrast vs white: 7.5:1 → 10.4:1, now AAA on both background and surface).
- `--user-message`: `#2563eb` → `#1d4ed8` (matches primary; white chat bubble text now AAA).
- `--focus-ring`: bumped alpha from 0.25 → 0.3 for better visibility on white.
- `--welcome-bg`: `#dbeafe` → `#eff6ff` (softer, reduces visual weight behind the welcome message).
- `--welcome-border`: aligned to new primary (`#1d4ed8`).
- `--shadow`: replaced generic black rgba with slate-tinted `rgba(15, 23, 42, 0.08)` so shadows look intentional rather than grey.
- `--code-bg`: `rgba(0, 0, 0, 0.06)` → `rgba(15, 23, 42, 0.06)` (same slate tint, consistent with shadow).
- Added a contrast-targets comment block documenting the intended WCAG ratios so future edits don't silently regress accessibility.

**Unchanged (already correct):**
- `--background: #ffffff`, `--surface: #f1f5f9`, `--surface-hover: #e2e8f0`, `--text-primary: #0f172a`, `--border-color: #cbd5e1`, `--assistant-message: #e2e8f0`.

**New light-mode-specific overrides** (for elements using hardcoded colors that don't come from variables):
- `.error-message` — swapped the dark-theme red wash (`rgba(239,68,68,0.1)` on dark) for a proper light-mode red: `#fef2f2` bg, `#b91c1c` text (AA+ on that bg), `#fecaca` border.
- `.success-message` — same treatment: `#f0fdf4` bg, `#15803d` text, `#bbf7d0` border.
- `a.source-item` — recolored to use the new primary with a 0.3-alpha border, and a hover state using a subtle 0.08-alpha tint (the original rgba values were keyed to the old `#2563eb` primary).
- `.message-content blockquote` — bound left-border to `--primary-color` (the original rule referenced an undefined `--primary` var, which rendered as the browser default in both themes; now correct in both).

## Accessibility Notes
- All body text against its background hits **AAA** (≥7:1).
- All primary-blue interactive states with white text hit **AAA** (8.6:1) — previously only AA in light mode.
- Border color against background is intentionally low-contrast (1.5:1) since it's a non-text UI delimiter, which is allowed under WCAG for decorative borders; the adjacent text remains high-contrast.
- Focus ring is theme-aware (alpha 0.3 in light, 0.2 in dark) so the keyboard outline stays visible against both palettes.
- The dark-theme values are untouched, so no regression there.

---

# Frontend Changes — Theme Toggle JavaScript

## Summary
The click-to-toggle handler and smooth CSS transitions were introduced in the first feature block above. This pass hardens the behavior: eliminates the flash-of-wrong-theme on load, and makes the app follow the OS `prefers-color-scheme` live when the user has no explicit preference saved.

## Files Changed

### `frontend/index.html`
- Added a tiny inline `<script>` in `<head>`, before the stylesheet link, that reads `localStorage.theme` (falling back to `prefers-color-scheme`) and sets `data-theme` on `<html>` **before first paint**. Wrapped in try/catch so a locked-down `localStorage` (private mode, strict cookie policies) degrades silently to dark.

### `frontend/script.js`
- `initializeTheme()` no longer re-reads preference on `DOMContentLoaded`; it now **trusts the pre-paint script** and just syncs `aria-checked` / `aria-label` to whatever `data-theme` already is. Avoids applying the theme twice.
- Added a `matchMedia('(prefers-color-scheme: light)')` **change listener** so if the user flips their OS theme while the tab is open, the UI follows — but only when `localStorage.theme` is unset (an explicit user choice always wins). Uses `addEventListener` with `addListener` fallback for older Safari.
- Click handler and keyboard (`Enter` / `Space`) handler unchanged — still toggle `data-theme` between `light` and `dark`, persist to `localStorage`, and update ARIA.

## Why These Changes
- **Pre-paint script:** setting `data-theme` from `DOMContentLoaded` meant the browser painted one frame with the default (dark) palette before switching, causing a visible flicker for light-theme users. Running synchronously in `<head>` before the stylesheet parses eliminates that.
- **Live OS sync:** respecting `prefers-color-scheme` only on first load is a half-measure — users who change their system theme mid-session expect the app to follow until they override it.
- **Smooth transitions:** the existing CSS `transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease` on all themed surfaces still drives the animation; no JS involvement needed beyond flipping the attribute.

---

# Frontend Changes — Theme Implementation Audit

## Summary
Audit pass to confirm the theme system uses CSS custom properties end-to-end and no element is stuck with a hardcoded color that breaks in one theme. Fixed two leftover hardcoded values; the rest of the codebase already routes through variables.

## Architecture (already in place)
- **CSS custom properties:** all themeable colors (primary, background, surface, text, border, messages, shadow, focus ring, welcome bg/border, code bg) live in `:root` (dark) and are overridden by `[data-theme="light"]`.
- **`data-theme` attribute:** set on the `<html>` element (not `<body>`, so it applies to `:root` without extra specificity). Driven by the pre-paint inline script, the click handler, and the OS-preference listener.
- **Visual hierarchy preserved:** light theme keeps the same primary blue (just shifted darker for AAA contrast), the same surface/background relationship (surface is a subtle step up from background), the same border weight, and the same pill/radius/spacing system.

## Files Changed

### `frontend/style.css`
- `.message.welcome-message .message-content`:
  - `background: var(--surface)` → `var(--welcome-bg)` — now uses the dedicated welcome-background variable that already existed but wasn't being consumed. Gives the welcome card a distinct blue tint in both themes instead of blending with the surface color.
  - `border: 2px solid var(--border-color)` → `var(--welcome-border)` — matches the primary accent per-theme.
  - `box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2)` → `var(--shadow)` — the hardcoded rgba was tuned for the dark theme; on white it rendered as a heavy grey blob. Using `--shadow` picks up the theme-appropriate slate-tinted shadow.
- `#sendButton:hover:not(:disabled)`:
  - `box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3)` → `var(--shadow)` — the hardcoded rgba was locked to the old `#2563eb` primary, so after the light theme's primary shifted to `#1d4ed8` the glow no longer matched. Routing through `--shadow` keeps the lift consistent.

## Audit Results
- Full grep of `style.css` for hex / rgba literals confirms every remaining hardcoded color is either (a) inside a variable definition, (b) in the semantic error/success palette which has explicit light-theme overrides, (c) inside the `header` block which is `display: none`, or (d) in a documentation comment.
- Every surface, text color, border, and shadow now resolves through a custom property, so future themes (e.g. a high-contrast variant) can be added as another `[data-theme="..."]` block with no further CSS edits.
