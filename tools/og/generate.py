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
    print("ok", p["id"])
print("done ->", OUT)
