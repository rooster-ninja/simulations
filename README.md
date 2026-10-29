# Simulations

Small interactive browser simulations, hosted on GitHub Pages:
https://rooster-ninja.github.io/simulations/

| Simulation | Link |
| --- | --- |
| Moon, Earth's shadow and the gegenschein | [moon-shadow/](https://rooster-ninja.github.io/simulations/moon-shadow/) |
| Seestar S30 star plate: how big is an arcsecond? | [seestar-star-plate/](https://rooster-ninja.github.io/simulations/seestar-star-plate/) |
| Plumb line curvature test | [plumb-line-test/](https://rooster-ninja.github.io/simulations/plumb-line-test/) |
| Plumb line test review | [plumb-line-review/](https://rooster-ninja.github.io/simulations/plumb-line-review/) |
| Disc model quasar test (WIP) | [disc-model-quasars/](https://rooster-ninja.github.io/simulations/disc-model-quasars/) |
| Celestial theodolite: planar prediction | [celestial-theodolite/](https://rooster-ninja.github.io/simulations/celestial-theodolite/) |
| Triangulation chain: baseline to check base | [triangulation-chain/](https://rooster-ninja.github.io/simulations/triangulation-chain/) |

## Layout

```
/
├── index.html          landing page listing every simulation
├── .nojekyll           serve files as-is (no Jekyll processing)
└── <sim-name>/
    ├── index.html      the simulation, self-contained
    └── README.md       what it shows, how it works, known limits
```

Each simulation lives in its own folder and is served at
`https://rooster-ninja.github.io/simulations/<sim-name>/`.

## Adding a simulation

`main` is the only publishing branch: GitHub Pages serves it, and every
simulation branch starts from it and merges back into it.

1. **Branch from `main`.** `git checkout -b <sim-name> origin/main`.
2. **Folder.** Short, lowercase, hyphenated name, e.g. `tides/`.
3. **Page.** `index.html`, self-contained (inline CSS/JS, no build step), with
   `og:title`, `og:description` and `theme-color` meta tags and
   `<a href="../">← All simulations</a>` at the top.
4. **Theme.** Research-note style, as in `celestial-theodolite/` and
   `triangulation-chain/`: cream background, Source Serif 4 headline, IBM Plex
   Mono blue eyebrow, numbered panels (`1 · TITLE`), formulas under figures,
   tables with right-aligned numbers and small-caps headers, a dark
   "Sources for this page (pages and quotes)" panel at the end. Light and
   dark mode.
5. **Content rules.** Raw source values; error bars on every result; results
   stated as fallible findings to a sigma level; a methods panel, an
   error-budget panel and the sources panel. No Wikipedia sources.
6. **Folder README.** `README.md`: what it shows, how it works, errors used,
   simplifications, sources. Data files go in `data/`, scripts in `scripts/`.
7. **Landing page.** Add a card to the root `index.html` and a row to the
   table above.
8. **Check it.** Open the page locally (or render it headless), step through
   every control, and confirm the console shows no errors.
9. **Pull request into `main`,** review, merge. The page is live at
   `https://rooster-ninja.github.io/simulations/<sim-name>/` a minute or two
   later.

## Publishing

In the repo's **Settings → Pages**, set **Source** to *Deploy from a branch*,
branch `main`, folder `/ (root)`. The repo must be public on a free plan.
