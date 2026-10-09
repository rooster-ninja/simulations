# Simulations

Small interactive browser simulations, hosted on GitHub Pages:
https://rooster-ninja.github.io/simulations/

| Simulation | Link |
| --- | --- |
| Moon, Earth's shadow and the gegenschein | [moon-shadow/](https://rooster-ninja.github.io/simulations/moon-shadow/) |
| Seestar S30 star plate: how big is an arcsecond? | [seestar-star-plate/](https://rooster-ninja.github.io/simulations/seestar-star-plate/) |

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

1. Create a folder with a short, lowercase, hyphenated name, e.g. `tides/`.
2. Put the page in it as `index.html`. Keep it self-contained (inline CSS/JS),
   and include `og:title` / `og:description` meta tags so links preview nicely
   in Discord.
3. Optionally add `<a href="../">← All simulations</a>` near the top.
4. Add a `README.md` in the folder describing the model and its simplifications.
5. Add a card for it in the root `index.html` and a row in the table above.

## Publishing

In the repo's **Settings → Pages**, set **Source** to *Deploy from a branch*,
branch `main`, folder `/ (root)`. The repo must be public on a free plan.
