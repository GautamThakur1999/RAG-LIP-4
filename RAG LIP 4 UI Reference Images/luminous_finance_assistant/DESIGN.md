---
name: Luminous Finance Assistant
colors:
  surface: '#faf8ff'
  surface-dim: '#d8d9e9'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f2ff'
  surface-container: '#ecedfd'
  surface-container-high: '#e6e7f7'
  surface-container-highest: '#e0e1f1'
  on-surface: '#181b26'
  on-surface-variant: '#3c4a43'
  inverse-surface: '#2d303c'
  inverse-on-surface: '#eff0ff'
  outline: '#6b7b72'
  outline-variant: '#bacac1'
  surface-tint: '#006c4f'
  primary: '#006c4f'
  on-primary: '#ffffff'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#2fe0aa'
  secondary: '#5c5f60'
  on-secondary: '#ffffff'
  secondary-container: '#e1e3e4'
  on-secondary-container: '#626566'
  tertiary: '#934b07'
  on-tertiary: '#ffffff'
  tertiary-container: '#ffa15b'
  on-tertiary-container: '#733800'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#e1e3e4'
  secondary-fixed-dim: '#c5c7c8'
  on-secondary-fixed: '#191c1d'
  on-secondary-fixed-variant: '#444748'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb785'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#713700'
  background: '#faf8ff'
  on-background: '#181b26'
  surface-variant: '#e0e1f1'
  background-white: '#FFFFFF'
  border-subtle: '#EBECEF'
  text-main: '#000000'
  surface-gray: '#F8F9FA'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Hanken Grotesk
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
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-bold:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1200px
  gutter: 24px
  margin-desktop: 64px
  card-padding: 32px
  stack-gap: 16px
---

## Brand & Style
The design system is engineered to project a sense of **unshakeable trust, radical clarity, and effortless intelligence**. Tailored for a Mutual Fund FAQ Assistant, the aesthetic avoids the clutter of traditional banking for a modern, streamlined experience that makes complex financial data feel approachable.

The design style is **Corporate Modern with Minimalist leanings**. It prioritizes vast negative space to reduce cognitive load, utilizing a "Card-First" architecture to modularize information. The interface feels light and airy, punctuated by a signature vibrant green that signifies growth and technical precision.

## Colors
The palette is anchored by a high-vibrancy "Growth Green" used strategically for primary actions and success states. The background is a crisp, pure white to ensure maximum contrast for text.

- **Primary Green (#00D09C):** Reserved for primary buttons, active states, and brand-defining accents.
- **Grays:** A tiered system of neutrals. `#444748` is used for secondary headings and high-priority body text, while `#7C7E8C` serves for helper text and iconography.
- **Borders:** Extremely subtle light grays (`#EBECEF`) are used to define card boundaries without creating visual noise.

## Typography
The system uses a dual-font strategy. **Hanken Grotesk** is used for headlines to provide a sharp, contemporary professional feel. **Inter** is used for all functional body and UI text due to its exceptional legibility in data-dense financial contexts.

For the FAQ assistant, prioritize the `body-lg` scale for chat bubbles to ensure the assistant's responses are comfortable to read for all age demographics. Tracking is slightly tightened on headlines to maintain a structured, sturdy appearance.

## Layout & Spacing
The layout follows a **Fixed Grid** model on desktop, centered within the viewport. Content is housed within a main container with a maximum width of 1200px to prevent excessive line lengths in text-heavy assistant responses.

A strict 8px spacing scale is applied. Assistant messages and user queries should follow a vertical stack with a `stack-gap` of 16px. Large-format sections (like the FAQ search and result cards) use generous `card-padding` of 32px to reinforce the minimalist, premium feel of the brand.

## Elevation & Depth
This design system avoids heavy drop shadows in favor of **Tonal Layers and Ambient Depth**.

1.  **Level 0 (Background):** Pure white `#FFFFFF`.
2.  **Level 1 (Cards/Bubbles):** Raised slightly via a very soft, diffused shadow: `0px 4px 20px rgba(0, 0, 0, 0.04)`.
3.  **Level 2 (Hover/Active):** Increased depth for interactive elements: `0px 8px 30px rgba(0, 0, 0, 0.08)`.

Borders are used as secondary depth indicators, specifically a 1px solid line in `#EBECEF` for input fields and non-interactive container segments.

## Shapes
The shape language is defined by large, friendly radii that evoke safety and modernity. 

- **Primary Containers:** 16px (`rounded-xl`) for main assistant chat windows and FAQ cards.
- **Interaction Elements:** 8px (`rounded-md`) for buttons and input fields.
- **Chat Bubbles:** 12px (`rounded-lg`) for assistant responses, with a sharp corner on the anchor side to indicate the speaker.

## Components

### Buttons
Primary buttons use a solid `#00D09C` fill with white text and no border. Hover states should darken the green slightly. Secondary buttons use a transparent background with a 1px border of `#EBECEF` and primary green text.

### Input Fields
Search bars and query inputs should be tall (min 56px) with a subtle light-gray background (`#F8F9FA`). On focus, the border transitions to a 2px stroke of the primary green.

### Chat Bubbles (Assistant)
Assistant bubbles use the `surface-gray` background with `text-main`. User bubbles use the `primary-color` with white text to clearly distinguish between the two.

### FAQ Cards
Cards should be designed with high-contrast headlines and secondary text for descriptions. Include a "Quick Link" chip at the bottom of the card using `label-md` styling.

### Chips/Tags
Used for "Suggested Questions." These are pill-shaped, using a light tint of the primary green as a background and the full-strength primary green for the text.