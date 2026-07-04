# Every Ball Ever — web

SvelteKit shell + the R0 particle-morph spike: one `THREE.Points` field of
~316k deliveries, scroll-scrubbed between a free field and season columns,
demand-mode rendered (the GL loop provably stops when scrolling stops).

## Commands

```bash
cd web
npm install        # once
npm run dev        # dev server → http://localhost:5173
npm run build      # static production build → web/build/
npm run preview    # serve the production build locally
npm run check      # svelte-check / TypeScript strict
```

Useful flags:

- `http://localhost:5173/?hud=1` — dev HUD: frames-rendered counter (stops when
  scrolling stops — the demand-mode proof), scrub FPS, point count, data mode.
- `BASE_PATH=/iplprogress npm run build` — reproduces the GitHub Pages subpath
  build locally (CI does this automatically).

## Data

The page fetches the R0 contract files from `static/data/` (emitted by the
Python pipeline — never hand-edited here):

```
meta.json · groups.json · group_ids.u16 · attrs.u8
```

If they're missing, **dev** builds fall back to a synthetic 316,388-point field
(flagged in the console + HUD); **production** builds show an integration
error overlay instead.

## Deploying (GitHub Pages)

Pushing to `main` runs `.github/workflows/deploy.yml`: Node 22 → `npm ci` →
`BASE_PATH=/<repo-name> npm run build` → assert the subpath made it into
`build/index.html` → upload `web/build` → deploy to Pages.

One-time owner setup (two clicks):

1. **Create the GitHub repository** (e.g. `iplprogress`) and push `main`.
2. **Enable Pages via Actions:** repo → Settings → Pages → *Build and
   deployment* → Source: **GitHub Actions**.

The site then lives at `https://<user>.github.io/<repo>/`. All internal asset
and data URLs go through SvelteKit's `base` path, so the subpath just works.

> Note: the workflow deploys whatever is committed. `web/static/data/` must be
> committed for the field to assemble in production — check the repo root
> `.gitignore` doesn't swallow it (an unanchored `data/` pattern would).
