# Detection-test measurement harness

Produces the real numbers behind `../pass-rate.py` (the chart in
*"How browser fingerprinting catches your scraper"*). It runs three Selenium
setups — vanilla, `selenium-stealth`, and `undetected-chromedriver` — against
two self-hosted, open-source detectors plus a transparent automation-tells
panel, and reports:

- **Automation-tells panel** (`tells.html`) — 17 concrete signals the post
  discusses (`navigator.webdriver`, `$cdc_` props, plugins, WebGL renderer,
  `productSub`, permissions consistency, error-stack cleanliness, …), scored as
  % passed.
- **BotD** (`botd.html`, FingerprintJS, MIT) — binary bot verdict.
- **CreepJS** — count of locally-detected "lies". Its headline *trust score*
  needs CreepJS's own API, so a self-hosted copy can't produce it; the local lie
  count is what's measurable offline.

Everything is self-hosted on `localhost`, so nothing hammers third-party
anti-bot services (consistent with the post's ethics section).

## Run it

```bash
# 1. Python deps
python -m venv .venv && . .venv/bin/activate
pip install selenium selenium-stealth undetected-chromedriver setuptools

# 2. Self-host BotD (this dir) — serves botd.html + tells.html on :8901
npm init -y && npm install @fingerprintjs/botd
python -m http.server 8901   # in this directory, background it

# 3. Self-host CreepJS on :8902 (prebuilt bundle, no build step)
git clone --depth 1 https://github.com/abrahamjuliot/creepjs.git
( cd creepjs/docs && python -m http.server 8902 )   # background it

# 4. Measure (N trials; default 1)
python runner.py 3
```

Results are written to `results/results.json`. Transfer the stable figures into
`../pass-rate.py` and regenerate the SVG.

## Reproducibility notes

- Measured on 2026-06-29, Chrome 149.0.7827.155, Linux, headful on a real X
  display, single machine / single IP.
- `undetected-chromedriver` is pinned with `version_main=149` to match the
  installed Chrome (it otherwise fetches the latest patched driver).
- Across 3 trials the BotD verdicts and CreepJS lie counts were identical every
  run; the tells panel varied only on vanilla's window-outer check (a
  window-manager quirk, not an automation tell): 14–15 / 17.
- These are a snapshot of one environment on one day, not a benchmark.
