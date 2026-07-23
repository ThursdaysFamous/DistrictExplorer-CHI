# Handoff 3: Implementation Fixes + School Cards (chidistricts.com — all metros)

## Overview
Third package; extends **Handoff 1** (`docs/design_handoff_county_board_card/`, County Board card, ids 3a–3d) and **Handoff 2** (`docs/design_handoff_card_system/`, card types 4a–4e). It corrects issues found in the first implementation pass and finishes the school cards. Reference designs are **turns 5, 6 and 8** (ids 5a–5d, 6a, 8a–8b) in the bundled `Info Card Explorations.dc.html` (earlier turns kept for context; turn 7 is superseded by turn 8).

Applies to all three metros (CHI, NYC, SF) unless noted.

## About the Design Files
Design references created in HTML — recreate in the app's existing vanilla-JS/inline-style card framework, not code to paste. Exact values are inline in the file.

## 5a — Layer color system (regression fix)
The colored "shadow" tying each card to its map layer was lost. Restore it, derived from the layer's theme color (`layerColor`):
- Left accent: `border-left: 3px solid layerColor` (no longer always blue)
- Shadow: `0 1px 2px rgba(0,0,0,.05), 0 3px 14px -4px layerColor@45%`
- Header dot: `layerColor`; ID pill: `color: layerColor` on `layerColor@9%` background
- Checkbox stays app blue `#1d5fd6`; links stay `#1a56c4`/`#123c8a` hover
- State overrides from Handoff 2 §4e still win: error accent `#c2410c`, empty accent `#d1d5db`

## 5b — ID pill + header format audit (regression fix)
- The header identifier pill is **universal**: every layer whose result has an identifier renders it top-right. Missed examples: Chicago Judicial Subcircuit ("Subcircuit 12"); several NYC and SF layers. Pill copy per type: "District 6" · "Subcircuit 12" · "Ward 11" · "Precinct 43" · "IL‑14" · "60564". No identifier → no pill (never an empty one).
- Header title: always the layer name at 16px/700/`#111827`. Some cards still ship the old 13px grey title — retire it everywhere, all metros.

## 5d — Details default
All `<details>` groups (committees, offices) are **closed by default** on every card, desktop and mobile. Remove any `open` attributes from Handoff 1/2 implementations.

## 6a — CPS zone cards (data display rules)
- Title-case school names and addresses from the raw ALL‑CAPS feed ("WATERS" → "Waters"; expand "HS" → "High School" when the full name is known, else leave as-is)
- Collapse contiguous grade lists to a range: "K, 1, 2, …, 8" → "K–8"; the range becomes the header pill (replaces trailing it after the address)
- Body row: school name 14.5px/700 + one contact line (address · links)
- "School profile ↗" sits bottom-right in the footer, opposite Pin (like "Official directory")

## 8a/8b — School Location (nearest 3) rebuild
Replaces the current numbered-list card.
- **Filter chips (8a):** the four type sub-checkboxes become toggle chips (no checkbox glyph): type dot 8px + label + count. On = `typeColor@12%` fill, `typeColor@35%` border, dark-tinted label. Type colors keep the existing map palette (Private green, Elementary purple, Middle amber, High teal).
- **Rows:** type dot + name 14px/700 + secondary line 12px ("High · 9–12" in type color, then "· address"); right-aligned distance pill in the type color (`typeColor@10%` bg). Numbering and the "Nearest schools, straight-line distance:" lede are dropped — order implies rank.
- **Footer:** footnote 11.5px/`#9aa3b2`: "Straight‑line distance. 'Private' = no CPS‑published grade band (parochial/independent); type inferred from grade range."
- **Filtered-off state (8b):** off chip = dashed `#d1d5db` border, grey dot, struck grey label, count kept. Header suffix flips "(all, incl. private · nearest 3)" → "(2 of 4 types · nearest 3)". List recomputes nearest 3 from remaining types. Footer swaps footnote for "Hiding N schools (Type, Type)." + "Show all" reset chip. Toggling is client-side only; persist chip state per session if trivial.

## Files
- `Info Card Explorations.dc.html` — implement turns 5, 6, 8. Turn 7 is an earlier chip draft superseded by turn 8; turns 1–4 are Handoffs 1–2.
- Counts/distances/school data in mocks are illustrative — always render real query results.
