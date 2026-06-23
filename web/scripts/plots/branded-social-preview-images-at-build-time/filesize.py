"""PNG file size before/after PNG8 palette optimization: flat vs photographic.

Numbers are REAL measurements taken on this machine (ImageMagick 6.9.12 Q16):

* "flat" is the actual branded OG card rendered by tools/og/project.html via
  headless Chrome (a gradient + text card).
* "photo" is a 1200x630 plasma+Gaussian-noise image standing in for a
  photographic source (continuous tone, lots of unique colors).

For each input we measure three encodings:
  - original truecolor PNG (Chrome's output / 24-bit)
  - PNG8 palette, dithering DISABLED  (-dither None -colors 256)
  - PNG8 palette, dithering ENABLED   (default Riemersma -colors 256)

Reproduce with:
  google-chrome --headless=new --window-size=1200,630 --screenshot=flat.png \
      'file:///.../tools/og/project.html?name=...&tagline=...'
  convert -size 1200x630 plasma:fractal -attenuate 0.6 +noise Gaussian photo.png
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
original = [307490 / KB, 4284369 / KB]
nodither = [63156 / KB, 586726 / KB]
dither = [82277 / KB, 586156 / KB]

x = np.arange(len(groups))
w = 0.26

fig, ax = plt.subplots()
ax.bar(x - w, original, w, label="Truecolor PNG (Chrome output)", color=PALETTE[0])
ax.bar(x, nodither, w, label="PNG8, dither off (the trick)", color=PALETTE[2])
ax.bar(x + w, dither, w, label="PNG8, dither on (default)", color=PALETTE[1])

# Log scale: the photographic bars are ~14x the flat ones, so a linear axis
# would crush the flat group into invisibility.
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
