# Pre-migration search baseline (chidistricts.com)

**What this is.** The last Google Search Console export from the `chidistricts.com` property
before the domain moved to districtry.com, pulled by the operator on **2026-08-24** (Web
search, last 6 months — the property's data covers 2026-07-12 onward, the site's first
indexed day).

**Why it is committed.** A GSC property cannot be renamed and its history cannot be moved to
another property. The `chidistricts.com` property keeps this data for a rolling 16 months and
then loses it; the new `districtry.com` property starts empty and is never backfilled. So this
file is the only durable record of what the site ranked for before the move, and the only
baseline a later "did the migration cost us anything?" question can be measured against.
Keep the old property verified — do not delete it — but do not rely on it.

## Totals

| | Clicks | Impressions | CTR | Avg position |
|---|---|---|---|---|
| All pages | 51 | 1572 | 3.24% | 12.35 (US) |

## Indexed pages, and where each one went

This table is the redirect map. Every row is a URL Google had indexed with real impressions;
the "now" column is where that content lives after R2.3 (`/il/`) and R5 (districtry.com).

| Old URL | Clicks | Impr. | Pos. | Now |
|---|---|---|---|---|
| `chidistricts.com/` | 50 | 1,245 | 12.76 | `districtry.com/` (forwards) |
| `chidistricts.com/school-board.html` | 1 | 65 | 9.38 | `districtry.com/il/school-board.html` |
| `nyc.chidistricts.com/` | 0 | 143 | 38.64 | `districtry.com/ny/` (forwards) |
| `sf.chidistricts.com/` | 0 | 58 | 42.59 | `districtry.com/ca/` (forwards) |
| `chidistricts.com/police-district.html` | 0 | 37 | 19.43 | `districtry.com/il/police-district.html` |
| `chidistricts.com/sources.html` | 0 | 14 | 18.07 | `districtry.com/il/sources.html` |
| `chidistricts.com/county-board.html` | 0 | 10 | 12.6 | `districtry.com/county-board.html` |

**The four `/il/` rows were 404ing after the cutover** — 126 impressions' worth of indexed
pages landing on nothing. Squarespace forwards the old host WITH the path intact, so the
forward arrives at districtry.com correctly; the paths had simply moved under `/il/` and
nothing held the old ones. The root-level redirect shells (`sources.html`,
`police-district.html`, `school-board.html`, `county-board.html`) exist to catch exactly
those four.

## Top queries at the baseline

The demand is phrased as a question, and the site ranked page 1 for the head terms while its
title said none of those words — the finding that drove the whole SEO change.

| Query | Clicks | Impr. | Position |
|---|---|---|---|
| what district am i in | 4 | 52 | 6.02 |
| find my district | 2 | 211 | 7.30 |
| find my district chicago | 0 | 77 | 8.01 |
| my district | 0 | 37 | 6.30 |
| what is my district | 0 | 20 | 6.75 |
| what chicago district am i in | 0 | 16 | 10.81 |
| which chicago school board district am i in? | 0 | 12 | 3.33 |
| what's my district | 1 | 6 | 2.67 |
| what ward and district am i in | 1 | 5 | 7.40 |
| chicago police find my district | 0 | 6 | 8.33 |

**Sibling-city demand landed on the wrong property.** `what district am i in nyc` (5 impr,
pos 56.6), `nyc district` (4, 42.3), `san francisco what district am i in` (3, 53.7) and
~40 more NYC/SF phrasings were all being answered by the *Illinois* page. That is what the
`/ny/` and `/ca/` titles, FAQs and landing pages are for.

## Devices

| | Clicks | Impressions | CTR | Position |
|---|---|---|---|---|
| Mobile | 30 | 566 | 5.30% | 6.83 |
| Desktop | 16 | 960 | 1.67% | 22.38 |
| Tablet | 5 | 13 | 38.46% | 4.92 |

Mobile converts at **3x desktop's CTR** and ranks far better — consistent with GoatCounter,
where ~60% of visits are phones.

## Daily series

| Date | Clicks | Impr. | Date | Clicks | Impr. |
|---|---|---|---|---|---|
| 2026-07-12 | 0 | 0 | 2026-08-02 | 2 | 43 |
| 2026-07-13 | 0 | 11 | 2026-08-03 | 4 | 55 |
| 2026-07-14 | 0 | 16 | 2026-08-04 | 2 | 52 |
| 2026-07-15 | 1 | 17 | 2026-08-05 | 3 | 58 |
| 2026-07-16 | 0 | 15 | 2026-08-06 | 1 | 53 |
| 2026-07-17 | 0 | 13 | 2026-08-07 | 2 | 60 |
| 2026-07-18 | 4 | 14 | 2026-08-08 | 2 | 26 |
| 2026-07-19 | 0 | 6 | 2026-08-09 | 1 | 55 |
| 2026-07-20 | 1 | 27 | 2026-08-10 | 1 | 81 |
| 2026-07-21 | 1 | 23 | 2026-08-11 | 1 | 52 |
| 2026-07-22 | 0 | 27 | 2026-08-12 | 2 | 41 |
| 2026-07-23 | 0 | 15 | 2026-08-13 | 1 | 45 |
| 2026-07-24 | 0 | 22 | 2026-08-14 | 1 | 39 |
| 2026-07-25 | 0 | 13 | 2026-08-15 | 1 | 16 |
| 2026-07-26 | 1 | 30 | 2026-08-16 | 1 | 33 |
| 2026-07-27 | 1 | 46 | 2026-08-17 | 1 | 23 |
| 2026-07-28 | 0 | 40 | 2026-08-18 | 0 | 23 |
| 2026-07-29 | 0 | 44 | 2026-08-19 | 1 | 18 |
| 2026-07-30 | 2 | 51 | 2026-08-20 | 2 | 56 |
| 2026-07-31 | 1 | 44 | 2026-08-21 | 0 | 107 |
| 2026-08-01 | 4 | 39 | 2026-08-22 | 6 | 90 |

Aug 21 is the impressions peak (107) and Aug 22 the clicks peak (6) — both **after** the
question-led title shipped to `/il/` on Aug 20, though far too early to read as causation.

## What to do with this

1. **Do not delete the `chidistricts.com` property.** Its data is viewable there for 16
   months from each day; this file outlives that.
2. **Run Change of Address** from the old property to the new one — it moves ranking signals,
   not data.
3. **Re-export before 2027-11** if a longer history matters; after that the old property's
   window has rolled past this range.
4. **Compare against this file**, not against memory, when asking whether the migration cost
   anything.
