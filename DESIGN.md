# Design System

<!-- impeccable:design-schema 1 -->

## Design Tokens

### Color Palette

- **Brand accent**: `brand-*` scale in `reservation-app/src/index.css` (`@theme`). `brand-600` `#1F5F6B` for primary buttons, `brand-300` for the active nav underline and links on dark. Used only for primary actions, links and the active nav item. Placeholder until we confirm CMKL's brand colour; change the scale in one place.
- **Chrome**: Nav bar `slate-900`. No other dark surfaces.
- **Canvas / Background**: Light `#F8FAFC` (`slate-50`), Dark `#0F172A` (`slate-900`)
- **Surface / Card**: Light `#FFFFFF` (`white`), Dark `#1E293B` (`slate-800`)
- **Borders**: Light `#E2E8F0` (`slate-200`), Dark `#334155` (`slate-700`)
- **Text Primary**: Light `#0F172A` (`slate-900`), Dark `#F8FAFC` (`slate-50`)
- **Text Secondary**: Light `#475569` (`slate-600`), Dark `#94A3B8` (`slate-400`) — minimum contrast ratio ≥ 4.5:1
- **Status Available**: text only, `green-700` / dark `green-400`
- **Status Closed / Conflict / Destructive**: `red-700` text, `red-600` destructive buttons / dark `red-400`

### Typography

- **Font Family**: IBM Plex Sans (`--font-sans`), IBM Plex Mono for IDs and times (`--font-mono`), loaded from Google Fonts in `index.html`; falls back to system UI offline.
- **Data & Numeric**: All room numbers, capacities, dates, and time ranges **MUST** use `tabular-nums` (`font-variant-numeric: tabular-nums`) to prevent shifting.
- **Hierarchy**:
  - Page Headings: `text-2xl font-bold tracking-tight`
  - Section Headings: `text-lg font-bold`; Modal Headings: `text-base font-semibold`
  - Data Labels: `text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400`
  - Body: `text-sm leading-relaxed`

### Spacing & Elevation

- **Elevation**: Flat to subtle depth (`shadow-sm` with 1px border `border-slate-200 dark:border-slate-700`). Banned: multi-layer heavy drop shadows (`shadow-2xl`) on standard utility cards.
- **Radius**: `rounded-lg` for cards and dialogs, `rounded-md` for inputs and buttons. Banned: giant bubbly pills (`rounded-full`) for standard content containers.

---

## Anti-Pattern Blacklist (De-Slop Rules)

1. **NO AI SaaS Gradient Headers**: Do not use `bg-gradient-to-r from-blue-600 to-indigo-600` or similar purple/blue fades. Use crisp solid institutional headers.
2. **NO `animate-bounce`**: Never use bounce or elastic keyframes. Use smooth cubic-bezier transitions (`cubic-bezier(0.16, 1, 0.3, 1)`).
3. **NO Nested Cards**: A card should not contain internal boxed sub-cards. Use clean typographical dividers, border separators, or lists.
4. **NO Pill Overdose**: Do not wrap every word or equipment attribute into a rounded pastel badge. Use clean text rows with bullet or dot separators.
5. **NO Icon Spam**: Do not put icons next to every label. Reserve icons for actionable buttons or critical status indicators.

---

## Accessibility Rules

1. All modals use `components/ModalShell.jsx`, which provides `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and dismiss on `Escape`.
2. All icon-only buttons must have descriptive `aria-label` attributes.
3. Form inputs must never use `display: none` (`hidden`); use `sr-only` with `focus-visible` rings for keyboard focusability.
4. Interactive touch targets must maintain minimum 40px–44px clickable areas.
