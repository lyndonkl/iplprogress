# R7a — Player search-a-name cards (storyboard for the design gate)

The final release's first half. A standalone product surface at `/players`: type any
of the ~937 names who ever batted or bowled in IPL (2008-2026) or WPL (2023-2026), and
get their card. This is the locked "later-release personalization feature" (memory:
"player search-a-name cards deferred to a later release"), now shipped.

It is a **new DOM/SVG route**, not the WebGL field (model: `web/src/routes/methods/+page.svelte`).
No three.js, no shared-field attribute ceiling. It links back INTO the Bowl (`/#bowl?b=<idx>`)
so the field and the cards are one product.

Everything here is computable from the existing Cricsheet corpus and already-emitted engine
artifacts. **No external data (ESPNcricinfo) is required or used** (that join is explicit
post-R7 scope).

R7a ships the cards. **R7b** (next) layers the credibility badges (Stabilization trust meters,
the shrinkage slider, Metric Half-Life freshness dials) onto both the cards and the sandbox.

---

## 0. The registry foundation (build this FIRST — correctness AND honesty)

The scout found there is **no player registry** and two disjoint id spaces:

- **Raw name strings** (columnar dicts, `srplus.json`, `entry.json`, sandbox `NameIndex`,
  the sandbox tour flags): **938** = union of 860 batter names + 672 bowler names (594 both).
- **Registry PIDs** (`info.registry.people`, used by `h2h.py` / `ch10.py` / `ch9.py`): **937**
  distinct who batted or bowled.

The shipped `meta.json` `n_players = 938` is **name-based and over-counts by ≥1** (at least one
player appears under two spellings). The Methods page currently claims "938 players counted by
registry ID, so a spelling change never becomes a second player" — **that claim is false today.**

**R7a fix:** a new `pipeline/registry.py` does one corpus pass over `info.registry.people` and emits
`web/static/data/players.json` — the join key everything else uses:

```
{ pid, name (canonical = last-seen display), aliases: [other spellings], leagues: ["ipl","wpl"],
  seasons: [2008..], teams: ["RCB", ...], role: "bat"|"bowl"|"all" (derived from balls faced/bowled),
  balls_faced, balls_bowled }
```

Then: correct `meta.n_players` to the registry PID count (937), and either make the Methods claim
true (it now is, once cards resolve by PID) or soften it. Every card element and the search box
key on `pid`; name→pid resolution (with aliases) happens once at the registry.

**Honesty win, not just plumbing:** the search box will never silently split one player into two
spellings or merge two players under one — the exact failure the current name-keyed count invites.

---

## 1. The search surface (`/players`)

**Mobile-first.** A single search field at the top: "Type a name." As you type, a ranked list of
matches (fuzzy over canonical name + aliases). Tap a name → their card loads (lazy per-player JSON,
or client-assembled from `srplus.json`/`entry.json` — see §7). Deep-linkable: `/players/<pid-or-slug>`.

Empty state (before typing): a few **suggested cards** (Kohli, Bumrah, a WPL star like Shafali
Verma, a cult name) as tappable chips — the same "never blank, land on something" principle as the
Bowl's tour flags. A "Surprise me" random-player button.

No login, no personalization storage beyond the URL. The card IS the shareable artifact
(`/players/v-kohli` is a link a mate opens).

---

## 2. Card anatomy (top → bottom, mobile column; desktop two-column)

**Header band**
- Canonical name, large.
- Role badge: **Batter / Bowler / All-rounder** (derived from balls faced vs bowled).
- League chips (IPL / WPL), team chips (RCB, RR, …), seasons active (2008-2024).
- One plain orienting line, data-bound, no adjectives: e.g. "RCB and RR · 2008-2024 · 7,263 balls
  faced · 431 bowled." A small "based on N balls" honesty note (the formal trust meter is R7b).
- If aliases exist: "also recorded as: V Kohli, Virat Kohli" (honest about the registry merge).

**Panel A — SR+ River (hero; batters and all-rounders)** — *data EXISTS*
- Their **SR+ by season** as a line, over a flat 100 baseline (the era-honest currency). Source:
  filter `srplus.json` rows (1,117 batter-season rows, name→pid) by this player; plot `srplus` across
  seasons. Peak season marked. Seasons with <100 balls faced are **absent** — shown as an honest gap
  with a faint "too few balls" tick, never interpolated.
- Orient first (voice guide): "100 is an average batter that season. Above the line means he scored
  faster than his peers did, priced against his own era, not today's."
- The whole point of the river is that 2008 Kohli and 2024 Kohli sit on the same axis.

**Panel B — Entry Map (batters and all-rounders)** — *aggregate EXISTS-as-rows, MUST-BUILD the blob*
- A small heatmap. x = over he walked in (0-19), y = wickets already down (0-9). Each of his career
  entries (from the 20,488-row `entry.json`, filtered to him) is a cell; the blob brightens where he
  most often came in. Source: aggregate `entry.json` rows by player.
- Reads his role at a glance: opener = a hot blob at over 0-1 / 0 wickets; a finisher = over 15+ / 4+
  down; a floater = a smear. Orient: "Each square is one innings. The brighter the blob, the more
  often he walked in there."
- Small annotation: median entry ball + typical position (e.g. "usually in around ball 3, opening").

**Panel C — Top Duels (everyone)** — *engine EXISTS, MUST-BUILD the per-player list*
- Two short ranked lists: **as batter** (bowlers he faced most) and **as bowler** (batters he
  dismissed/faced most), if applicable. Each row: opponent name, balls, runs, dismissals, and a
  **who-came-out-on-top** color from Engine #6's EB-shrunk dominance (red = batter won, blue = bowler
  won, pale = even; the exact `h2h.dominance` / `EBConstants.shrunk` machinery, μ≈1.3322, k≈51.2).
- Small duels are EB-pulled toward par (honest: 12 balls is not a verdict). Each row taps through to
  **that duel in the Bowl** (`/#bowl?b=<batIdx>&w=<bowlIdx>`).
- Source: `h2h.build_table()`, filter `.items()` by this player's pid on each side, sort by balls.

**Panel D — Teleporter (batters; the cross-era beat)** — *engine EXISTS, MUST-BUILD per-player call*
- Their **peak SR+ season**, re-priced to 2026, shown two honest ways: the **naive** transport (raw SR
  carried straight over — the fantasy) and the **percentile-honest** transport (where his rank among
  his own peers would land him among 2026's). The **gap between them is the exhibit**, with an
  uncertainty band. Uses the general `ch10.py` machinery (`_player_season`, `_translate`,
  `sr_at_pct` / `percentile_of`) called for this player.
- **Fallacies-guard hard line:** the card states "how far above his own era he was," NOT "he'd average
  X today." No definitive "modern twin." The honest band must be visibly ≤ the naive-vs-honest gap
  (same guardrail as Ch10, asserted at build). A link to the full Ch10 teleporter for the deep dive.
- Non-batters / thin batters: this panel is omitted rather than faked.

**Footer — See them in the Bowl** — *reuses R6b sandbox*
- A button: "See every ball he faced" → `/#bowl?b=<dictIdx>&v=1` (and/or `w=` for bowlers). The card's
  bridge back to the 316k-ball field. Reuses `buildFacetMask`'s existing batter/bowler facet.

**Bowler / all-rounder handling**
- Bowlers get a **bowling panel** in place of (or alongside) the batting hero: an economy / **TrueEcon**
  line by season (the SR+ mirror — runs saved vs expected; catalog line 380), wickets per season, a
  dismissal-kind mini (bowled/lbw/caught/stumped share), and the **Top Duels as bowler** list.
  - *Design-gate question Q1: build the bowler TrueEcon river in R7a (reuses the `par.py` conditional
    cells, a real but bounded pipeline add), or ship bowlers with raw economy + wickets in R7a and add
    TrueEcon in R7b? Recommendation: raw economy + wickets + duels in R7a; TrueEcon with the credibility
    layer in R7b, so R7a stays scoped.*
- All-rounders (594 players bat AND bowl) get both a batting hero and a bowling panel, whichever is
  richer on top.

---

## 3. Honesty rules (fallacies-guard + voice guide)

1. **Small samples read lightly.** A player with, say, 40 career balls gets a **stub card**: header +
   "small sample — read this lightly" + the raw line + the see-in-the-Bowl link, and the SR+ river /
   teleporter panels are suppressed (not faked). The formal per-stat trust meter arrives in R7b; R7a
   uses a plain balls-count floor (design-gate Q4: propose ~100 balls for the full card, matching
   `SRPLUS_MIN_BALLS`, else stub).
2. **WPL is priced against WPL, never "behind."** WPL players' SR+ is vs the WPL baseline; the league
   chip says WPL; the copy never compares a WPL number to a men's number without saying so. (Binding
   project rule.)
3. **Cross-era is a range, not a verdict.** The teleporter shows the gap + band; "how far above his own
   era," never a single "he'd be X today" number.
4. **The registry merge is disclosed** (aliases line), not hidden.
5. **No editorializing adjectives.** Orient plainly, let the numbers carry it (voice guide rule 3 + 5:
   plain gloss for SR+, entry, dominance, economy; "you"-with-swagger reserved for the one point per
   panel, never the orientation).
6. **Zero em dashes** anywhere on the surface (binding).

---

## 4. Voice (per research/voice-guide.md, binding)

- Orient then reveal in every panel's first line (what the axes/colors/dots are, before the point).
- One idea + one number per caption; extras to a footnote/tooltip.
- Plain glosses: SR+ = "faster than his peers, era-adjusted"; entry = "when he walked in"; dominance =
  "who came out on top"; economy = "runs he leaked an over"; TrueEcon = "runs saved vs an average bowler."
- "You/he" with a mate-on-the-couch warmth on the POINT; dead-plain on orientation.

---

## 5. What R7a ships vs defers to R7b

**R7a ships:** the registry, the search surface, the card (header + SR+ river + entry map + duel list
+ teleporter + see-in-the-Bowl), batter + bowler + all-rounder variants, the small-sample stub, WPL
handling, deep-link URLs, the Methods-page n_players fix.

**R7b adds (next):** Stabilization Points → a real per-stat **trust meter** on every card number and
sandbox leaderboard; the **shrinkage slider** (raw → True-Talent regressed, 80% CIs) on leaderboards
and the SR+ river; Metric Half-Life → a **freshness dial** on the teleporter ("this 2013-vs-2025
comparison keeps N% of its meaning"); bowler TrueEcon river (if deferred from R7a).

---

## 6. The card's data (what the pipeline emits for R7a)

1. `players.json` — the registry / search index: `[{pid, name, aliases, leagues, seasons, teams, role,
   balls_faced, balls_bowled}]`. Small (~tens of KB), can ship in the cold-open-excluded lazy set.
2. Per-player card payload — either (a) one `player_cards.json` bundle keyed by pid, or (b) lazy
   per-player files, or (c) **assembled client-side** from already-shipped `srplus.json` + `entry.json`
   + a small `duels_by_player` table + a `teleporter_percentiles` lookup. **Recommendation: (c) hybrid**
   — reuse `srplus.json` (river) and `entry.json` (entry map, aggregated client-side) directly; ship
   two small new tables: `duels_by_player.json` (top-N duels per pid with EB dominance) and
   `teleporter_lookup.json` (per-league-season SR percentile curve, so the teleporter runs client-side).
   Keeps payload tiny and out of the cold-open critical set (ledger `SANDBOX_SET` pattern).
3. `meta.json` — corrected `n_players` (937) + a `players` ledger block.

All byte-deterministic (sorted keys, integer-cent discipline where relevant). Registered in
`ledger.py` as its own budget check. Tested in `pipeline/tests/test_r7a.py` with recounted snapshot
constants (registry count, srplus row count, a spot-checked famous-player duel) + a mutation guard.

---

## 7. Open questions for the design gate

- **Q1 (bowler river):** TrueEcon river in R7a, or raw economy + wickets in R7a and TrueEcon in R7b?
  (Recommend the latter for scope.)
- **Q2 (teleporter compactness):** per-player card shows just the peak-season naive-vs-honest gap +
  band + a link to the full Ch10 teleporter, OR an embedded era dial? (Recommend the compact gap +
  link; the full dial is Ch10's job.)
- **Q3 (entry map for bowlers):** omit (bowlers get the bowling panel instead), or show a
  phase-of-bowling map? (Recommend omit for R7a.)
- **Q4 (small-sample floor):** full card at ≥100 balls (matches `SRPLUS_MIN_BALLS`), stub below?
- **Q5 (card delivery):** confirm the hybrid client-assembly (§6c) over shipping 937 per-player files.
- **Q6 (search ranking):** prefix + fuzzy over name+aliases; tie-break by career balls (so "V Kohli"
  ranks above an obscure namesake). Confirm.

## 8. Cognitive-design review asks

- Is the six-panel card too dense for a phone? Propose the collapse/priority order (what shows above
  the fold; what's a tap-to-expand).
- Entry-map heatmap legibility at ~320px: cell size, color ramp (CVD-safe, luminance-carried per the
  project's binding CVD rule), and whether a 20×10 grid needs binning to e.g. 10×6.
- SR+ river with gaps: how to show "no data this season" without implying a dip to zero.
- Duel-list dominance color: reuse the Ch9 bowler-blue / batter-red diverging ramp (luminance-safe),
  keep it consistent site-wide.
- The teleporter gap: make the honest band unmistakably the smaller, truer quantity (anti-overclaim).

---

## 9. DESIGN-GATE RESOLUTIONS (binding on the build)

The cognitive-design + fallacies-guard review is folded in here. This section is the build
contract; where it conflicts with the sketch above, this wins.

### 9.0 The signature-number honesty fix (accumulators)
SR+ measures SCORING PACE vs a player's own era, not overall greatness. Verified: V Kohli's
peak SR+ is **109 (2016)**, not a dramatic number, because his edge is average/volume, not
tempo. So the header must NOT lead with a bare "Peak SR+" that makes a legend look ordinary.
**Header signature = the unarguable volume facts FIRST, then the SR+ peak as tempo:**
`{teams} · {seasons} · {balls_faced} balls · {runs} runs · out once every {balls_per_dismissal}
balls · peak SR+ {peak} in {year}`. The dismissal-rate stat (balls faced / dismissals,
computed client-side from the columnar `wicket` flags) is what gives an accumulator his due.
SR+ is oriented as "how fast he scored vs his era," never as a greatness score. (Average+ is a
later add; do not build it in R7a.)

### 9.1 Layout & fold (MUST)
Header (with the signature line) + **SR+ River hero** are always visible above the fold. **Entry
Map, Top Duels, Teleporter each COLLAPSE behind a one-line teaser that already carries the
payload in words** (so a non-tapper still lands the point), e.g. "Where he came in: usually
around ball 3, opening. Tap to see." / "Biggest rivalry: 160 balls vs Jadeja. Tap for the list."
/ "How far above his own era he sat. Tap to re-price to 2026." See-in-the-Bowl is the always-
visible footer. Desktop: two columns (hero + teleporter left, entry + duels right), captions
beside/above plots never overlaying.

### 9.2 Entry Map (MUST)
Bin to **10 × 6 = 60 cells**. x = over walked in, 2-over bins `[0-1][2-3]...[18-19]` (preserves
powerplay-ends-after-bin-3 and death = last two bins). y = wickets down `0,1,2,3,4,5+`.
**Single-hue luminance ramp on sqrt(count)** (empty = no fill, background shows through; min ≈
`#3a2a1a`, max ≈ `#ffcf8f`; verify L* monotonic; cividis is the vetted fallback). **Outline all
60 cells at low opacity, fill only ≥1-innings cells** so absence ≠ a cold zero. One required
annotation: a callout on the brightest cell translating it to a role ("Walked in here most: over
1, none down. An opener."). Anchor-only axis ticks (powerplay/death). **Framing: "where he came
in / where his team sent him," never "chose"; "brighter = more often, not better."**

### 9.3 SR+ River (MUST)
Line, not bars. **Break the line with `d3.line().defined(d => d.hasData)`** at any season under
100 balls; never interpolate, never drop to baseline/zero. Gap ticks sit at a **neutral vertical
position (top margin), never near the value axis**; on tap "too few balls this season (under 100
faced)." No zero baseline (SR+ is an index around 100); y-domain roughly symmetric and clamped so
100 is always on screen (≈ `[max(60,min-pad), min(180,max+pad)]`). Solid muted 100 reference line
labeled with the **league-specific** baseline: "100 = an average IPL batter that season" (or WPL).
Faint luminance band (lighter above 100 / darker below) optional, a whisper. Peak marked, labeled
"biggest edge over his era." **Orient era-relative, NOT as improvement:** "Above 100 means he
scored faster than his peers that season. The line rising means he pulled further ahead of his
era, not that he simply scored more." No "up = better" arrow, no causal annotation.

### 9.4 Top Duels (MUST — revise the Ch9 reuse; hue-only FAILS the CVD rule)
Each row = a **diverging horizontal bar centered on a par midline**: extends **left toward the
batter** when the batter dominates, **right toward the bowler** when the bowler dominates.
**Direction rides SIDE, length rides MAGNITUDE (position channel, CVD-immune); hue (warm=batter /
cool=bowler) is REDUNDANT only, luminance-matched at equal magnitude.** Three distinct states:
real edge = filled, leaning, saturated; genuine even (≥ threshold balls, ~par) = filled, centered,
pale; **too few balls (below ~30, EB-pulled to par) = hollow/ghosted outline, "too few balls to
call."** Ball count on **every** row; EB-shrunk value drives bar length (a 12-ball fluke can't draw
a long bar). **Rank by balls, not wins** (no cherry-pick sort). Each row taps to that duel in the
Bowl (`/#bowl?b=&w=`). Reuse Engine #6 `dominance` / `EBConstants.shrunk` (μ≈1.3322, k≈51.2).

### 9.5 Teleporter (MUST — highest overclaim risk on the card)
One 2026-unit axis. **HONEST = a solid, bright, filled BAND (an interval), read first**; **NAIVE =
a dim hollow/dashed ghost, labeled "raw carry-over, ignores the era."** The gap gets a bracket +
one line: "The naive number pretends 2026 is his era. It isn't. Priced honestly against today's
batters, he lands in this band." **Copy is RANK-TRANSLATION only:** "Measured against his own era
he sat in the top X% of batters; put that same rank in 2026 and it lands here." **BAN the strings
"he'd average," "he would score," "modern twin," and any bare "= X today" on the card.** The band
width IS the uncertainty. **Assert at build: honest-band extent ≤ naive-vs-honest gap** (the Ch10
guardrail). Add "cross-era is a range, not a verdict." Link to Ch10 labeled "see how his era
compares," never "find his modern twin." Omit for non-batters / thin batters (don't fake).

### 9.6 WPL (MUST — binding project rule)
Every SR+/teleporter number names its **league-and-season baseline inline**. A WPL player
re-prices to **WPL 2026 only** ("priced against 2026 WPL batters"); never offer a men's/IPL
teleport for a WPL player. **No WPL-on-the-IPL-timeline copy on the card** (that is Ch6's authored
job). `registry.py` must guarantee **aliases never bridge a WPL and an IPL player** (disjoint
leagues, no shared pid).

### 9.7 Small samples (MUST)
Full card at **≥100 balls in the primary role**; stub below (header + "small sample, read this
lightly" + raw line + Bowl link; river/teleporter suppressed, not faked). **Per-panel
suppression**: a bowling panel needs ≥100 balls bowled or it is omitted (not shown confidently);
duels under ~30 balls hollow out. **"Based on N balls" is visible on every card, always.**

### 9.8 Bowler panel R7a (Q1)
Raw economy + wickets + Top-Duels-as-bowler. **Draw economy as a plain per-season line, NOT a
cross-era river**, labeled "Raw runs per over, not era-adjusted yet. The era-fair version comes
next." (TrueEcon river is R7b.)

### 9.9 Search (Q6)
Prefix matches rank above mid-string fuzzy; diacritic-insensitive; a secondary result line shows
role + league + seasons (disambiguate namesakes); alias hits show the canonical name with a muted
"matched: {alias}"; tie-break by career balls.

### 9.10 Delivery (Q5)
Hybrid client-assembly: reuse shipped `srplus.json` (river) + `entry.json` (entry map, aggregated
client-side) + two small new tables `duels_by_player.json` + `teleporter_lookup.json`; keep out of
the cold-open critical set (lazy, ledger sandbox-style block). **Measure the client-side
`entry.json` aggregation (20,488 rows) on first card paint; if it janks (>~200ms), precompute the
per-player entry blob into a table instead.**

### 9.11 Voice (MUST): zero em dashes everywhere; orient-then-reveal first line in every panel;
one idea + one number per caption; plain glosses (SR+, entry, dominance, economy); "you/he"-with-
swagger only on the point.

### 9.12 Confirmed decisions: Q1 raw-economy-in-R7a / TrueEcon-R7b · Q2 compact teleporter + link ·
Q3 omit bowler entry-map · Q4 ≥100-ball floor + per-panel suppression · Q5 hybrid client-assembly ·
Q6 as §9.9.
