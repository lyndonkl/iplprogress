# Verify — Every Ball Ever web app

How to run and drive this SvelteKit app to verify scene changes.

## Build / launch

```bash
cd web
npm run dev -- --port 5199   # dev server (base path is '' in dev)
# or: npm run build && npm run preview  (preview serves on 4173)
```

Real pipeline data lives in `web/static/data/` — the field loads it directly
in dev; if files are missing, dev builds fall back to a synthetic field
(console warns loudly).

## Driving the scroll story (browser)

- The story is one scroll timeline; scene sections are stacked `section.scene`
  elements whose heights are `scrollLength` vh (1vh = innerHeight/100).
  Compute a scene's scroll offset by summing prior sections' heights, or read
  `document.querySelectorAll('section.scene')[i].getBoundingClientRect()`.
- Scene progress = (scrollY − sectionTop) / sectionHeight (ScrollTrigger
  start 'top top', end 'bottom top').
- `window.scrollTo(0, y)` + ~400ms settle is enough to land a scrub state.
- Reader state: `ebe.sketch.v1`, `ebe.team.v1`, `ebe.progress.v1`,
  `ebe.footnotes.v1` in localStorage. Clear between flows —
  `ebe.footnotes.v1` reopens the footnote panel on reload by design.
- `?hud=1` shows the render-stats HUD (frames counter = demand-mode proof).

## Gotchas

- Multiple agent sessions may share the Chrome instance and run their own
  servers (4173 preview, etc.) — create your own tab, use your own port.
- Vite HMR from concurrent edits to `web/src` reloads the page mid-test and
  resets scroll; re-drive the flow after an unexpected jump to top.
- Full-page screenshots JPEG-crush DOM cards over the dense point field —
  use `zoom` on the card region before concluding something didn't render.
- `resize_window` / cmd+= zoom do not change `innerWidth` in this harness;
  mobile breakpoints (max-width 640px CSS, `w < 640` JS) need a real narrow
  window or devtools emulation.
- The You-Draw-It canvas: `left_click_drag` on the SVG draws (pointer capture
  + interpolation); a second drag continues from a new column.
