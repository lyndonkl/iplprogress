# Every Ball Ever

An interactive, scrollytelling exploration of how T20 cricket evolved across the
IPL (2008–2026) and WPL (2023–2026) — all 316,199 deliveries rendered as one
living particle field.

**Status:** R0 (data pipeline + particle-morph spike). See
[`research/experience-blueprint.md`](research/experience-blueprint.md) for the
full chapter map and release plan.

## Structure

- `pipeline/` — stdlib-Python build pipeline: flattens Cricsheet ball-by-ball
  JSON into the static data artifacts the site consumes (`web/static/data/`).
- `web/` — SvelteKit + three.js site. `cd web && npm install && npm run dev`.
- `research/` — the verified metrics catalog, data profile, presentation
  research, and the experience blueprint (single source of truth).
- `data/` — raw match JSON (not committed; download from
  [cricsheet.org](https://cricsheet.org/) — IPL and WPL ball-by-ball).

## Data attribution

Ball-by-ball data from [Cricsheet](https://cricsheet.org/), made available
under the [Open Data Commons ODbL](https://opendatacommons.org/licenses/odbl/1-0/).
The committed files under `web/static/data/` are derived from that data.
