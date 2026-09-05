# Visual Identity

![Guru Benchmark hero and social preview](../assets/guru-benchmark-hero.svg)

The repository hero represents the council as seven independent evidence nodes feeding one visible synthesis rather than seven portraits or personality brands.

## Visual QA — 2026-09-05

The canonical SVG was rendered with Google Chrome 148 at 1280 × 640 and inspected as a raster image.

- Pass: no clipping at any canvas edge.
- Pass: no headline, subtitle, card, node, or footer overlap.
- Pass: headline and primary labels have strong contrast.
- Pass: all seven council nodes and the central synthesis are visible and legible.
- Pass: no malformed glyphs, placeholder copy, white corners, or transparent-edge artifacts.
- Pass: left content and right council diagram remain visually balanced.
- Note: footer principles are intentionally secondary but remain readable at full social-preview size.

## Design contract

- **Canvas:** 1280 × 640, suitable for README display and social-preview rendering.
- **Palette:** near-black foundation, violet for analytical structure, mint for synthesis, amber for consequential clarification.
- **Typography:** system-safe sans serif; no external font dependency.
- **Accessibility:** high-contrast headline, meaningful SVG title/description, and descriptive README alt text.
- **Safety:** initials identify council positions without using likenesses, logos, quotations, or endorsement language.

The canonical editable asset is `assets/guru-benchmark-hero.svg`. `assets/social-preview.png` is its rendered 1280 × 640 counterpart for platforms that require raster upload.
