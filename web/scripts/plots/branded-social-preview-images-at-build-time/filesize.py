"""PNG file size before/after PNG8 palette optimization: flat vs photographic.

Numbers are REAL measurements taken on this machine (ImageMagick 6.9.12 Q16):

* "flat" is the actual branded OG card for the `weberist` project, rendered by
  tools/og/project.html via headless Chrome (a gradient + text card). Its
  no-dither PNG8 is the file shipped at web/public/images/og/weberist.png.
* "photo" is a real photograph (matplotlib's classic `grace_hopper.jpg` test
  image) fit to the same 1200x630 canvas: continuous tone, ~230k unique colors.
  An earlier draft used a synthetic plasma+Gaussian-noise image, but pure noise
  is incompressible as truecolor PNG (~4.2 MB), which inflated its apparent
  palette-reduction to ~86% and misrepresented how a real photo behaves.

For each input we measure three encodings:
  - original truecolor PNG (Chrome's output / 24-bit)
  - PNG8 palette, dithering DISABLED  (-dither None -colors 256)
  - PNG8 palette, dithering ENABLED   (default Riemersma -colors 256)

Reproduce with:
  # flat card (as tools/og/generate.py renders it, before the PNG8 step):
  google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
      --force-device-scale-factor=1 --window-size=1200,630 \
      --screenshot=flat.png --virtual-time-budget=4000 \
      'file:///.../tools/og/project.html?name=Weberist&tagline=...&role=...&stack=...'
  # photo (any real photograph fit to the card canvas):
  convert grace_hopper.jpg -resize 1200x630^ -gravity center -extent 1200x630 photo.png
  for s in flat photo; do
    convert $s.png -strip -dither None -colors 256 PNG8:$s-nodither.png
    convert $s.png -strip            -colors 256 PNG8:$s-dither.png
  done
  stat -c%s *.png
"""

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from _style import apply, save, PALETTE  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

apply()

# Measured bytes -> KB (1 KB = 1024 B).
KB = 1024.0
groups = ["Flat OG card\n(gradient + text)", "Photographic\n(continuous tone)"]
original = [303520 / KB, 763013 / KB]
nodither = [60079 / KB, 291784 / KB]
dither = [80070 / KB, 298829 / KB]

x = np.arange(len(groups))
w = 0.26

fig, ax = plt.subplots()
ax.bar(x - w, original, w, label="Truecolor PNG (Chrome output)", color=PALETTE[0])
ax.bar(x, nodither, w, label="PNG8, dither off (the trick)", color=PALETTE[2])
ax.bar(x + w, dither, w, label="PNG8, dither on (default)", color=PALETTE[1])

# Log scale: the photographic bars are several times the flat ones, so a linear
# axis would crush the flat group into invisibility.
ax.set_yscale("log")
ax.set_ylabel("File size (KB, log scale)")
ax.set_title("PNG8 palette optimization: flat graphics vs photos")
ax.set_xticks(x)
ax.set_xticklabels(groups)
ax.legend(loc="upper left")

# Annotate the percentage saved by the dither-off PNG8 step.
for i in range(len(groups)):
    saved = 100 * (1 - nodither[i] / original[i])
    ax.annotate(
        f"-{saved:.0f}%",
        xy=(x[i], nodither[i]),
        xytext=(0, 6),
        textcoords="offset points",
        ha="center",
        fontsize=9,
    )

out = save(
    fig,
    pathlib.Path(__file__).resolve().parents[3]
    / "src/assets/blog/branded-social-preview-images-at-build-time/filesize.svg",
)
print(f"wrote {out}")
