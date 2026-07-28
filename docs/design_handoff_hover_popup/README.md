# Handoff 4: Map Hover Popup (chidistricts.com — all metros)

## Overview
Fourth package. Rebuilds the shared **hover snapshot** (the dark popup that follows the cursor over the map) on the card system shipped in Handoffs 1–3, and specifies what it shows when the hover target is a **POI pin** rather than a polygon stack. Reference designs are **9a** (polygon stack) and **10a** (pinned office) in the bundled `Info Card Explorations.dc.html`. 9b/9c and 10b/10c are alternates that were considered and are kept in the file for context — **do not implement them**.

Engine surfaces touched: `hover-explorer` (rendering) only. No layer-contract change, no new fields — `hoverName`, `hoverOfficial`, `pointOfInterest` and the `hoveredPoi` token all keep their current behavior. Applies to all three metros (CHI, NYC, SF).

## About the Design Files
Design references created in HTML — recreate in the app's existing vanilla-JS/inline-style environment, not code to paste. Exact values are inline in the file.

## 9a — Polygon stack (the default hover popup)

**Surface.** Light, matching the result cards: `#fff`, `1px solid rgba(0,0,0,.08)`, radius 10px, shadow `0 10px 30px -10px rgba(20,25,40,.45), 0 1px 3px rgba(0,0,0,.1)`. Width 324px. 12px tail on the bottom edge, centered, `#fff` with the card's border on its two outer sides, pointing at the cursor. The dark plate is retired — hover and click now speak the same visual language.

**Row.** `display:grid; grid-template-columns:10px 1fr; gap:0 10px; padding:9px 14px`, divided by `1px solid #f1f3f7`.
- **Dot** — 10px circle in the layer's `overlay.style.color`, `margin-top:4px` to sit on the label's baseline. Layers whose map color is white/near-white render a ringed dot instead (`background:#fff; border:1.5px solid #b9c0cc`) so they stay visible on a light surface.
- **Layer label** — 11.5px/600/`#6b7280`, the full layer name ("IL State Senate District"). Never colored: color is carried by the dot and pill only. This inverts today's popup, where the colored layer name outranks the person and the blue/red labels fail AA on near-black.
- **ID pill** — right-aligned in the label row, 11.5px/700, `color: layerColor` on `layerColor@10%`, radius 999, padding `1px 7px`. **Bare identifier** ("20", "33"), not "Ward 33" — the adjacent label already names the layer. This is the one place the pill copy differs from the cards (Handoff 3 §5b). No identifier → no pill.
- **Officeholder** — second grid row in column 2, 14px/700/`#111827`. Sourced from `hoverOfficial` exactly as today.
- **Municipality (and any layer whose identifier is a name)** — the place name goes in the **pill**, like every other identifier: pill "Chicago city", officeholder line "Brandon Johnson". Do not concatenate them into the name line.

**Footer.** `1px solid #e8eaef` top rule, 11px/`#9aa3b2`, "Click for full cards" — the same footnote token as the card system.

**Order.** Unchanged: federal → state → county → municipal → ward.

## 10a — Hovering a pinned office location

Fires on the POI-pin path: a `pointOfInterest` pin (school address, board office) or a `registerNearestPointLayer` dot, i.e. whenever `hoveredPoi` is set (engine `v1.0.6`). The pin becomes the popup's **subject**, promoted above the stack.

**Promoted header block.** Padding `11px 14px`, `background: layerColor@6%`, `border-bottom:1px solid layerColor@18%`, top radius 10px.
- **Eyebrow** — the layer label, 10px/700, `letter-spacing:.05em`, uppercase, `color: layerColor` ("Office location", "Police Station").
- **Pin glyph** — 13px, `border-radius:50% 50% 50% 0` rotated −45°, filled `layerColor`, 4.5px white center dot. Same glyph as the map marker, half size.
- **Name** — 14.5px/700/`#111827`: the segment of `line()` before the first " — ".
- **Address** — 12px/`#6b7280`, the remainder of `line()`, prefixed by a 7px grey pin glyph (`#9aa3b2`). This **replaces the CSS `📍`** — the card system carries no emoji. Renders only when an address exists (keep the `v1.0.6` guard; never an orphan glyph).
- **Pill** — the layer's identifier, or the distance for a nearest-N layer ("1.2 mi").

**Stack below.** The 9a rows, with two changes:
- The pin's **own layer row** keeps full contrast and is tied to the header: `border-left:2px solid layerColor`, `background: layerColor@5%`, padding `9px 14px 9px 12px`, label `#4b5563`.
- **Every other row** de-emphasizes: padding `8px 14px`, officeholder drops to 13.5px/600/`#4b5563`, pill tint to `layerColor@9%`. Labels stay 11.5px/600/`#6b7280` — do **not** lighten them further; `#8b93a1` measures 3.09:1 and fails AA.

**Footer.** "Click for the County Board card" — name the pin's layer, since a click on a pin opens that card.

**Districts shown are the pin's, not the cursor's.** The stack must be computed at the pin's coordinates (the reference shows Ward 42 / the County Building, not the Ward 33 point under the cursor). If that recomputation is not cheap on hover, ship 10c instead for pins outside the selected point's districts — never label the cursor's districts as the office's.

## States to keep
- **No polygon row for the pin's layer** (station / library / post-office dots): render the promoted header block alone, no stack — reference **10c**. Optional, and the only piece of 10c that is in scope.
- **No address** on the hovered feature: address line absent, not empty.
- **Dot-to-dot hovering**: unchanged token-identity guard from `v1.0.6` — moving between pins must not blank the popup.
- **Touch**: unchanged `hoverCapable` gate — a tap never pops the popup.

## Files
- `Info Card Explorations.dc.html` — implement **9a** and **10a** (plus 10c's standalone block). Turns 1–8 are Handoffs 1–3, kept for context.
- Names, districts and addresses in the mocks are illustrative — always render real query results.
