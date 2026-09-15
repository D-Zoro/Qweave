---
name: Quantum Synthetic
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bbc9cd'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#859397'
  outline-variant: '#3c494c'
  surface-tint: '#2fd9f4'
  primary: '#8aebff'
  on-primary: '#00363e'
  primary-container: '#22d3ee'
  on-primary-container: '#005763'
  inverse-primary: '#006877'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#ffd6a3'
  on-tertiary: '#462b00'
  tertiary-container: '#ffb13b'
  on-tertiary-container: '#6e4600'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#a2eeff'
  primary-fixed-dim: '#2fd9f4'
  on-primary-fixed: '#001f25'
  on-primary-fixed-variant: '#004e5a'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#ffddb5'
  tertiary-fixed-dim: '#ffb957'
  on-tertiary-fixed: '#2a1800'
  on-tertiary-fixed-variant: '#643f00'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.1em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin: 32px
  container-padding: 20px
---

## Brand & Style
The design system is engineered for high-fidelity quantum computing interfaces. The brand personality is scientific, precise, and forward-looking, evoking the atmosphere of a deep-space laboratory or a high-end IDE. 

The aesthetic leverages **Glassmorphism** and **High-Tech Minimalism**. Interfaces should feel like "light projected onto dark glass." Use semi-transparent layers, subtle glowing borders, and sharp, monospaced data points to emphasize the complexity and precision of quantum state monitoring. The emotional response should be one of sophisticated control and focused clarity.

## Colors
The palette is rooted in a deep-space spectrum.
- **Base Surfaces:** Use `#0f172a` (Slate 950) for the application backdrop. 
- **Containers:** Use `#1e1b4b` (Dark Indigo) with varying opacities for frosted glass effects.
- **Accents:** 
    - **Cyan (#22d3ee):** Used for primary actions, active quantum states, and stable metrics.
    - **Violet (#8b5cf6):** Used for secondary logic, probabilistic data, and complex algorithmic paths.
- **Functional:** Success states use Cyan; Warning states use a desaturated Amber; Error states use a high-vibrancy Pink/Red to contrast against the cold blue background.

## Typography
This design system employs a dual-font strategy:
- **Inter** handles all UI scaffolding, navigation, and instructional text. It provides a clean, human-readable foundation that balances the technical nature of the content.
- **JetBrains Mono** is reserved for all variable data, quantum coordinates, code snippets, and telemetry. This separation ensures that the user's eye can immediately distinguish between "interface" and "computation."

All labels (`label-caps`) should be set in uppercase to reinforce the scientific instrumentation aesthetic. Use `data-lg` for large-scale metric monitoring.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a strictly enforced 4px base unit. 
- **Structure:** Use a 12-column grid for desktop views. Containers should utilize `backdrop-filter: blur(12px)` to maintain legibility over complex background gradients.
- **Rhythm:** Dense data displays should use 8px (2 units) of internal padding, while editorial or high-level dashboard views should use 24px (6 units) to allow for "visual breathing room."
- **Breakpoints:** 
  - Mobile (<768px): 4 columns, 16px margins.
  - Tablet (768px - 1280px): 8 columns, 24px margins.
  - Desktop (>1280px): 12 columns, 32px margins.

## Elevation & Depth
Depth is created through **Luminance and Translucency** rather than traditional drop shadows.
- **Level 0 (Floor):** Deep Slate (#0f172a).
- **Level 1 (Panels):** Dark Indigo (#1e1b4b) at 40% opacity with a 1px solid border at 10% white opacity.
- **Level 2 (Popovers/Modals):** Dark Indigo at 80% opacity with a subtle Cyan outer glow (`box-shadow: 0 0 15px rgba(34, 211, 238, 0.1)`).
- **Interactions:** When an element is hovered, the border opacity should increase from 10% to 40% white, and the backdrop blur should intensify.

## Shapes
The shape language is **Soft (0.25rem)**. This provides a precision-engineered look that avoids the aggressive sharpness of brutalism while remaining more professional and "industrial" than fully rounded consumer apps. 

Use sharp 0px corners only for data-grid cells and code blocks. All glass containers and primary buttons must use the `rounded-md` (0.25rem) or `rounded-lg` (0.5rem) standard to maintain a modern, refined silhouette.

## Components
- **Buttons:** Primary buttons use a solid Cyan fill with black text. Secondary buttons use a transparent background with a 1px Cyan border and Cyan text. Use a subtle "glow" transition on hover.
- **Cards/Containers:** Must feature `backdrop-filter: blur(16px)` and a top-down linear gradient border (White 20% to White 5%) to simulate light hitting the edge of a glass pane.
- **Input Fields:** Darker than the container background. Use JetBrains Mono for the input text. On focus, the border should glow with the Primary Cyan.
- **Status Chips:** Small, monospaced text with a leading "dot" icon. Stable states = Cyan; Fluctuating = Violet; Critical = Pink.
- **Data Visualizations:** Use thin strokes (1px or 1.5px). Avoid solid area fills; use gradients that bleed into transparency to maintain the "light-based" aesthetic.
- **Telemetry Lists:** Use alternating row highlights at 5% white opacity. Ensure all numerical columns are right-aligned using JetBrains Mono for tabular lining.