# Sanad — brand identity reference

## Name
**Sanad** (سند) — Arabic for the verified chain of transmission that authenticates a report back to its source. Maps directly to the product's audit-trail architecture.

## Color palette
| Role | Hex | RGB |
|---|---|---|
| Primary — Sanad navy | `#1C3D36` | 28, 61, 54 |
| Accent — Sanad gold | `#C9A227` | 201, 162, 39 |
| Text/secondary — gray | `#6B7278` | 107, 114, 120 |
| Background — cream (banners only) | `#F7F5F0` | 247, 245, 240 |

Navy carries the wordmark and the long stroke of the mark. Gold is used sparingly — only the short stroke of the checkmark — as a single accent, never as a background or text color.

## Typography
- **Wordmark / UI**: Liberation Sans (metric-compatible with Arial/Helvetica) — use system Arial or Helvetica Neue if unavailable.
- **Arabic accent**: Amiri (Naskh) — use Noto Naskh Arabic as a substitute.
- Sentence case throughout. No all-caps, no italics in the wordmark.

## The mark
A circular seal containing two interlocking strokes — a short gold link and a long navy link — that together form a checkmark. Two readings, intentionally: a verification mark (compliance, approval) and a linked chain (sanad, chain of custody).

**Usage rules**
- Minimum clear space around the mark: half the icon's diameter on all sides.
- Minimum size: do not display the icon below 24px — it stops resolving.
- Do not recolor the mark outside the palette above.
- Do not separate the gold and navy strokes into different opacities or add a drop shadow/gradient.
- Icon-only (no wordmark) at any size below ~120px — the wordmark is illegible before the icon is.

## File index

| File | Format | Size | Use |
|---|---|---|---|
| `sanad_icon_transparent.png` | PNG, transparent | ~758×758 | Master icon — favicons, app icons, social avatars generally |
| `sanad_icon_on_navy.png` | PNG, solid navy bg | 1024×1024 | Icon on dark/solid backgrounds |
| `sanad_logo_master.svg` | SVG, vector, fonts embedded | 400×400 | Source file — resize losslessly, hand to a designer or print shop |
| `sanad_lockup_vertical_transparent.png` | PNG, transparent | ~431×712 | Vertical lockup (icon over wordmark) — title slides, letterhead |
| `sanad_logo_horizontal_transparent.png` | PNG, transparent | ~1037×422 | Horizontal lockup — website header, email signature, deck footer |
| `sanad_linkedin_page_logo_300x300.png` | PNG, transparent | 300×300 | **LinkedIn Company Page logo slot** — icon only, per LinkedIn's spec |
| `sanad_linkedin_cover_1128x191.png` | PNG, full-bleed | 1128×191 | **LinkedIn Company Page cover banner** |

## Font note
The `sanad_logo_master.svg` file has Amiri and Liberation Sans embedded directly in it (subsetted to only the characters used, ~20KB added). This was a deliberate fix: the first version of this file referenced fonts by name only, so it displayed correctly only on machines that had Amiri installed — anywhere else, the viewer silently substituted its own default Arabic font, which is why the Arabic name looked different depending on where the file was opened. Embedding the font removes that dependency; the file now renders identically everywhere without requiring anything installed locally. Text stays fully editable (position, size, color) — only the glyph shapes are now guaranteed rather than best-effort.

## Setting up the LinkedIn page
1. Page logo: upload `sanad_linkedin_page_logo_300x300.png` as-is.
2. Cover image: upload `sanad_linkedin_cover_1128x191.png` as-is — it's sized exactly to LinkedIn's company-page banner spec, no cropping needed.
3. Tagline field: "Verified shariah compliance for Islamic fintech."
4. About section: lead with the wedge, not the technology — what the product screens, who it's for, and the human-review step. Save the axiom/Z3 architecture detail for the website, not the LinkedIn summary.
