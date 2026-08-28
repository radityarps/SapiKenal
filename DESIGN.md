---
name: Agro-Humanist Mobile
colors:
  surface: "#fbf9f5"
  surface-dim: "#dbdad6"
  surface-bright: "#fbf9f5"
  surface-container-lowest: "#ffffff"
  surface-container-low: "#f5f3f0"
  surface-container: "#efeeea"
  surface-container-high: "#e9e8e4"
  surface-container-highest: "#e4e2df"
  on-surface: "#1b1c1a"
  on-surface-variant: "#424841"
  inverse-surface: "#30312e"
  inverse-on-surface: "#f2f1ed"
  outline: "#737970"
  outline-variant: "#c2c8bf"
  surface-tint: "#466648"
  primary: "#2f4e32"
  on-primary: "#ffffff"
  primary-container: "#466648"
  on-primary-container: "#bee2bc"
  inverse-primary: "#acd0ab"
  secondary: "#735a3a"
  on-secondary: "#ffffff"
  secondary-container: "#fddab1"
  on-secondary-container: "#785e3e"
  tertiary: "#663d0e"
  on-tertiary: "#ffffff"
  tertiary-container: "#825424"
  on-tertiary-container: "#ffcfa5"
  error: "#ba1a1a"
  on-error: "#ffffff"
  error-container: "#ffdad6"
  on-error-container: "#93000a"
  primary-fixed: "#c7ecc6"
  primary-fixed-dim: "#acd0ab"
  on-primary-fixed: "#02210a"
  on-primary-fixed-variant: "#2f4e32"
  secondary-fixed: "#ffddb5"
  secondary-fixed-dim: "#e2c19a"
  on-secondary-fixed: "#291801"
  on-secondary-fixed-variant: "#594325"
  tertiary-fixed: "#ffdcbf"
  tertiary-fixed-dim: "#f8ba81"
  on-tertiary-fixed: "#2d1600"
  on-tertiary-fixed-variant: "#673d0e"
  background: "#fbf9f5"
  on-background: "#1b1c1a"
  surface-variant: "#e4e2df"
typography:
  headline-lg:
    fontFamily: Quicksand
    fontSize: 28px
    fontWeight: "700"
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Quicksand
    fontSize: 22px
    fontWeight: "600"
    lineHeight: 28px
  headline-sm:
    fontFamily: Quicksand
    fontSize: 18px
    fontWeight: "600"
    lineHeight: 24px
  body-lg:
    fontFamily: Quicksand
    fontSize: 16px
    fontWeight: "500"
    lineHeight: 24px
  body-md:
    fontFamily: Quicksand
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 20px
  label-lg:
    fontFamily: Quicksand
    fontSize: 14px
    fontWeight: "600"
    lineHeight: 20px
    letterSpacing: 0.1px
  label-sm:
    fontFamily: Quicksand
    fontSize: 12px
    fontWeight: "500"
    lineHeight: 16px
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  margin-mobile: 20px
  gutter-mobile: 12px
---

## Brand & Style

The design system is built upon an "Agro-Humanist" aesthetic, specifically tailored for a mobile-first agricultural context. The brand personality is grounded and deeply reliable, evoking the calmness of a managed landscape. It avoids the coldness of traditional tech by utilizing organic textures and a warm, low-contrast palette that reduces cognitive load for users who may be operating in high-glare or high-stress outdoor environments.

The style leans into **Minimalism with Tactile influences**, using soft surfaces and natural color transitions rather than harsh dividers. The emotional response should be one of stewardship and tranquility—positioning the app as a digital companion rather than a complex tool.

## Colors

The palette is derived from natural elements: vegetation, soil, and sunlight.

- **Primary (Sage Green):** Used for main actions and representing "Healthy" states. It provides a sense of growth and vitality.
- **Secondary (Earthy Brown):** Used for accents, navigation elements, and specialized shadows to maintain warmth.
- **Surface (Soft Cream):** The foundation of the UI, chosen to reduce eye strain compared to pure white.
- **Status Tones:** We use a semantic scale for livestock health. Healthy is Sage, Warning (PMK/FMD) is a Warm Amber-Orange, and Critical (LSD/Terracotta) is a muted Terracotta Red.

All text should default to **Espresso Black** to ensure high legibility against the cream background while maintaining a softer contrast than true black.

## Typography

This design system utilizes **Quicksand** exclusively to leverage its rounded terminals, which mirror the organic shapes found in nature.

- **Headlines:** Should use Bold or Semi-Bold weights to create clear entry points for the eye.
- **Body Text:** Uses Medium weight (500) as the default for better legibility on mobile screens, as the rounded nature of the font can appear thin at Regular weights.
- **Scaling:** For mobile devices, the largest headline is capped at 28px to ensure it does not wrap awkwardly on smaller handsets.

## Layout & Spacing

The layout follows a **Fluid Grid** model optimized for Android handheld devices.

- **Margins:** A standard 20px outer margin is maintained to keep content away from the screen edges and curved glass.
- **Rhythm:** An 8px linear scale is used for vertical rhythm, though 4px increments are allowed for tight component internals (like icon-to-label spacing).
- **Safe Areas:** Bottom navigation and floating action buttons (FABs) must respect the Android gesture navigation bar, providing at least 24px of bottom padding.

## Elevation & Depth

In this design system, depth is expressed through **Ambient Shadows** and **Tonal Layering** rather than high-contrast light sources.

- **Shadow Character:** Shadows are soft and diffused, utilizing a tint of the Secondary Earthy Brown (`rgba(62, 54, 46, 0.08)`) instead of pure gray. This ensures the "warmth" of the UI is maintained even in the shadows.
- **Surface Tiers:**
  - **Level 0:** Cream Background.
  - **Level 1:** Cards and Sheets. They use a subtle shadow to appear "resting" on the surface.
  - **Level 2:** Buttons and Floating Action Buttons. They use a slightly more pronounced shadow (8px blur) to indicate interactivity.

## Shapes

The shape language is ultra-rounded and organic, avoiding sharp corners entirely to maintain the humanist tone.

- **Primary Containers:** Cards, modals, and large buttons use a 24px (rounded-3xl) radius.
- **Bottom Sheets:** Use a distinctive 32px radius on the top-left and top-right corners to emphasize the "soft pull-up" metaphor.
- **Inputs:** All text fields and search bars are **fully pill-shaped (rounded-full)** to maximize the approachable, friendly aesthetic.

## Components

- **Buttons:** Primary buttons use the Sage Green background with white text. They should be 56px in height for easy thumb-tapping.
- **Cards:** Use the Soft Cream background but are defined by the brown-tinted ambient shadow. Padding inside cards should be 20px.
- **Input Fields:** Pill-shaped with a 1px border of Warm Grayish-Green. When focused, the border thickens to 2px in Sage Green.
- **Chips:** Used for livestock tags or health status. Use a 16px radius and a light tint of the status color (e.g., a very pale green for "Healthy").
- **Bottom Sheets:** These are the primary navigation pattern for adding data. They must include a "handle" at the top—a 32px wide, 4px thick rounded bar in a light brown tint.
- **Icons:** Use organic line-art with rounded caps and joins. Avoid "filled" icons unless indicating an active state in the bottom navigation bar.
