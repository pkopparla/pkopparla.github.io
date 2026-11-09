#!/usr/bin/env python3
"""Make the margin sprites in images/sprites/ from the purchased pixel art pack.

The art is "Tree Pixel PNG (400 Files).zip": 400 numbered 3500x3500 transparent PNGs
(01_starlight-pine-leaf..., 400_oak-tree...). Keep it in drafts/, which git ignores,
so the paid originals are never published. Only the small images this script makes
are committed. The pack's PDF lists print uses only; check the seller's licence
before using other art from it.

To swap sprites, change the numbers in SPRITES (and TREES, for the big ones), then
run from the repo root:

    python3 -I tools/make_sprites.py "drafts/Tree Pixel PNG (400 Files).zip"

and preview the site locally before committing. Pick by number from a contact sheet;
the file names describe each one. Pillow is the only dependency (pip install pillow).

What it does to each sprite, in order:
  1. Crop to the visible art (alpha > 16), then shrink to fit 384px (Lanczos).
  2. Simplify ("chunky, no outline"): shrink to a coarse grid of 3 CSS px per art
     pixel (box filter), make edges hard (alpha > 110), boost saturation 1.2x and
     reduce to 8 colours with no dithering. Trees are 81px tall, everything else 57px.
  3. Scale back up 3x with nearest neighbour, then 2x again so the PNGs stay sharp on
     dense screens. style.css shows them at half size.

Then it lays them out:
  rows.png         Margin tile, 6 columns x 4 rows at 112 x 96 CSS px, repeated by CSS.
                   Rows are slices of SPRITES (0-5, 6-11, 3-8, 9-11 + 0-2), nudged
                   12px left or right on alternate rows. A half-step stagger would
                   slice the sprite at the tile edge next to the column.
  band-top.png     Phone layout, one row above the content (SPRITES 0-5).
  band-bottom.png  One row below the content (SPRITES 6-11).

Each sprite appears twice in the tile, so look-alikes (two round green trees, two
mushrooms) can end up next to each other or stacked; fix it by reordering SPRITES.
"""

import io
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageEnhance

# Pine, apple, sacred fig, banana, hollow oak, acorn,
# autumn tree, orange, toadstool, pear tree, mushroom, plum
SPRITES = [396, 319, 212, 303, 39, 399, 152, 315, 175, 292, 63, 287]
TREES = {396, 212, 39, 152, 292}

PX, COLOURS, SATURATION = 3, 8, 1.2     # CSS px per art pixel, palette size
TREE_H, SMALL_H = 81, 57                # sprite heights in CSS px
X = 2                                   # render scale
STEP, ROW, COLS = 112, 96, 6            # tile cell size in CSS px, columns
OUT = Path(__file__).resolve().parent.parent / "images" / "sprites"


def load(z, n):
    name = next(f for f in z.namelist() if f.rsplit("/", 1)[-1].startswith(f"{n}_"))
    im = Image.open(io.BytesIO(z.read(name))).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox())
    im.thumbnail((384, 384), Image.LANCZOS)
    return im


def chunky(im, height):
    pad = 2
    gh = round(height / PX) - 2 * pad
    gw = max(1, round(im.width * gh / im.height))
    small = im.resize((gw, gh), Image.BOX)
    alpha = small.getchannel("A").point(lambda v: 255 if v > 110 else 0)
    rgb = ImageEnhance.Color(small.convert("RGB")).enhance(SATURATION)
    q = rgb.quantize(colors=COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGBA")
    q.putalpha(alpha)
    out = Image.new("RGBA", (gw + 2 * pad, gh + 2 * pad))
    out.alpha_composite(q, (pad, pad))
    return out.resize((out.width * PX * X, out.height * PX * X), Image.NEAREST)


def place(canvas, im, cx, cy):
    canvas.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def tile(rows, sprites):
    W, H = STEP * COLS * X, ROW * len(rows) * X
    c = Image.new("RGBA", (W, H))
    for r, nums in enumerate(rows):
        off = 12 if r % 2 else -12
        for i, n in enumerate(nums):
            cx = ((i * STEP + STEP / 2 + off) % (STEP * COLS)) * X
            for dx in (-W, 0, W):  # wrap sprites that straddle the edge
                place(c, sprites[n], cx + dx, (r * ROW + ROW / 2) * X)
    return c


def band(nums, sprites):
    c = Image.new("RGBA", (STEP * len(nums) * X, 88 * X))
    for i, n in enumerate(nums):
        place(c, sprites[n], (i * STEP + STEP / 2) * X, 44 * X)
    return c


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    Image.MAX_IMAGE_PIXELS = None
    with zipfile.ZipFile(sys.argv[1]) as z:
        sprites = {n: chunky(load(z, n), TREE_H if n in TREES else SMALL_H) for n in SPRITES}
    s = SPRITES
    OUT.mkdir(parents=True, exist_ok=True)
    tile([s[0:6], s[6:12], s[3:9], s[9:] + s[:3]], sprites).save(OUT / "rows.png", optimize=True)
    band(s[:6], sprites).save(OUT / "band-top.png", optimize=True)
    band(s[6:], sprites).save(OUT / "band-bottom.png", optimize=True)
    print(f"make_sprites.py: wrote rows.png, band-top.png, band-bottom.png to {OUT}")


if __name__ == "__main__":
    main()
