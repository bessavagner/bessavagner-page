#!/usr/bin/env python3
"""Render a branded 1200x630 OG card per project from content/projects.json."""
import json
import pathlib
import subprocess
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
TPL = (ROOT / "tools/og/project.html").as_uri()
OUT = ROOT / "web/public/images/og"
OUT.mkdir(parents=True, exist_ok=True)


def optimize_png(path):
    """Re-encode as a palette (PNG8) image — cuts these flat/graphic cards ~70%
    (≈300KB -> ≈90KB) with no visible loss. No-op if ImageMagick is unavailable."""
    try:
        # -dither None: these cards are flat (text + gradient), so dithering only
        # adds noise and *grows* the file. Without it, PNG8 stays clean and tiny.
        subprocess.run(
            ["convert", str(path), "-strip", "-dither", "None",
             "-colors", "256", f"PNG8:{path}"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass


data = json.load(open(ROOT / "content/projects.json"))
for p in data["projects"]:
    params = urllib.parse.urlencode({
        "name": p["name"],
        "tagline": p["tagline"],
        "role": p.get("role", ""),
        "stack": ",".join(p.get("stack", [])[:5]),
    })
    out = OUT / f"{p['id']}.png"
    subprocess.run(
        ["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", "--force-device-scale-factor=1",
         "--window-size=1200,630", f"--screenshot={out}",
         "--virtual-time-budget=4000", f"{TPL}?{params}"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    optimize_png(out)
    print("ok", p["id"])
print("done ->", OUT)
