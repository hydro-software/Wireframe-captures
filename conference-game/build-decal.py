"""
Build the naia arcade-panel decal in three variants, each in two formats:

* naia-arcade-panel-54.5x11cm-300dpi.png/.pdf
    Trim size 6437 x 1299 px @ 300 dpi (54.5 x 11 cm)
    1.5 cm magenta border on all 4 sides

* naia-arcade-panel-54.5x11cm-300dpi-no-border.png/.pdf
    Same canvas size, dark bg + stars + logo full-bleed (no magenta).
    Logo is enlarged (1 cm top/bottom + 2 cm left/right padding).

* naia-arcade-panel-54.5x11cm-300dpi-no-border-warp.png/.pdf
    Same as above but the grid lines bend outward from the centre to
    reinforce the warp-speed feel of the radial star trails.

Each variant is also exported with a 3 mm print bleed (afloop) as
*-bleed.png + .pdf. The bleed file is 6507 x 1369 px (55.1 x 11.6 cm) -
trim line is 35 px in from each edge, with all artwork extending into
the bleed area.

Run from this folder:
    python build-decal.py

Inputs:
    naia_logo_870x360_canvas.png
"""

import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

DIR = Path(__file__).parent
LOGO = DIR / 'naia_logo_870x360_canvas.png'

# --- Geometry: 54.5 x 11 cm @ 300 dpi ---
DPI = 300
CM_TO_PX = DPI / 2.54
W = round(54.5 * CM_TO_PX)            # 6437 — trim width
H = round(11.0 * CM_TO_PX)            # 1299 — trim height
BLEED = round(0.3 * CM_TO_PX)         # 35 px = 3 mm bleed on each side
B_W = W + 2 * BLEED                   # 6507 — bleed width
B_H = H + 2 * BLEED                   # 1369 — bleed height
BORDER = round(1.5 * CM_TO_PX)        # 177 px = 1.5 cm magenta frame
LOGO_PADDING = round(0.5 * CM_TO_PX)  # 59 px = 0.5 cm gap from magenta to logo
MAGENTA = (255, 0, 255)

# Output paths
OUT = {
    'border':           ('naia-arcade-panel-54.5x11cm-300dpi.png',
                         'naia-arcade-panel-54.5x11cm-300dpi.pdf'),
    'border-bleed':     ('naia-arcade-panel-54.5x11cm-300dpi-bleed.png',
                         'naia-arcade-panel-54.5x11cm-300dpi-bleed.pdf'),
    'no-border':        ('naia-arcade-panel-54.5x11cm-300dpi-no-border.png',
                         'naia-arcade-panel-54.5x11cm-300dpi-no-border.pdf'),
    'no-border-bleed':  ('naia-arcade-panel-54.5x11cm-300dpi-no-border-bleed.png',
                         'naia-arcade-panel-54.5x11cm-300dpi-no-border-bleed.pdf'),
    'warp':             ('naia-arcade-panel-54.5x11cm-300dpi-no-border-warp.png',
                         'naia-arcade-panel-54.5x11cm-300dpi-no-border-warp.pdf'),
    'warp-bleed':       ('naia-arcade-panel-54.5x11cm-300dpi-no-border-warp-bleed.png',
                         'naia-arcade-panel-54.5x11cm-300dpi-no-border-warp-bleed.pdf'),
}

print(f'Trim:  {W} x {H} px ({W/CM_TO_PX:.1f} x {H/CM_TO_PX:.1f} cm)')
print(f'Bleed: {B_W} x {B_H} px ({B_W/CM_TO_PX:.1f} x {B_H/CM_TO_PX:.1f} cm) — 3 mm bleed on each side')
print(f'Magenta border: {BORDER} px ({BORDER/CM_TO_PX:.2f} cm)')

# --- 1. Background generation (works at any canvas size) ---
DARK_NAVY = (14, 28, 42)
GRID_COLOR = (40, 95, 130)
GRID_PERIOD = 150
GRID_LINE_W = 2

def draw_orthogonal_grid(d, cw, ch, cx, cy):
    """Standard square grid centred on (cx, cy) inside a cw x ch canvas."""
    x = cx % GRID_PERIOD
    while x < cw:
        d.line([(x, 0), (x, ch - 1)], fill=GRID_COLOR, width=GRID_LINE_W)
        x += GRID_PERIOD
    y = cy % GRID_PERIOD
    while y < ch:
        d.line([(0, y), (cw - 1, y)], fill=GRID_COLOR, width=GRID_LINE_W)
        y += GRID_PERIOD

def draw_warp_grid(d, cw, ch, cx, cy, warp=0.35):
    """Grid where each line bends outward from (cx, cy)."""
    n_v = (cw // GRID_PERIOD) + 6
    for i in range(-n_v, n_v + 1):
        x_orig = cx + i * GRID_PERIOD
        dx = x_orig - cx
        x_edge = x_orig + dx * warp
        if max(x_orig, x_edge) < 0 or min(x_orig, x_edge) > cw:
            continue
        d.line([(x_edge, 0), (x_orig, cy), (x_edge, ch - 1)],
               fill=GRID_COLOR, width=GRID_LINE_W, joint='curve')
    n_h = (ch // GRID_PERIOD) + 6
    for i in range(-n_h, n_h + 1):
        y_orig = cy + i * GRID_PERIOD
        dy = y_orig - cy
        y_edge = y_orig + dy * warp
        if max(y_orig, y_edge) < 0 or min(y_orig, y_edge) > ch:
            continue
        d.line([(0, y_edge), (cx, y_orig), (cw - 1, y_edge)],
               fill=GRID_COLOR, width=GRID_LINE_W, joint='curve')

def draw_stars(layer, cw, ch, cx, cy, n_stars=1500, seed=20260507):
    """Warp-speed stars: bright cores leading outward, fading trails toward (cx, cy)."""
    sd = ImageDraw.Draw(layer)
    rng = random.Random(seed)
    palette = [
        (255, 230, 100),
        (255, 130, 200),
        (180, 240, 255),
        (160, 200, 255),
        (255, 255, 255),
        (200, 130, 255),
    ]
    TRAIL_SEGMENTS = 10
    for _ in range(n_stars):
        sx = rng.randint(0, cw - 1)
        sy = rng.randint(0, ch - 1)
        core = rng.choice([2, 2, 3, 3, 3, 4, 4, 5])
        base = rng.choice(palette)
        dx, dy = sx - cx, sy - cy
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            ang = rng.uniform(0, 2 * math.pi)
            nx, ny = math.cos(ang), math.sin(ang)
        else:
            nx, ny = dx / dist, dy / dist
        trail_len = rng.choice([18, 22, 26, 30, 34, 40, 46]) + core * 2
        for i in range(TRAIL_SEGMENTS, 0, -1):
            t = i / TRAIL_SEGMENTS
            tx = sx - nx * trail_len * t
            ty = sy - ny * trail_len * t
            size = max(1, round(core * (1 - t * 0.85)))
            alpha = int(220 * (1 - t) ** 1.6)
            if alpha < 4:
                continue
            sd.ellipse([tx - size, ty - size, tx + size, ty + size], fill=base + (alpha,))
        sd.ellipse([sx - core, sy - core, sx + core, sy + core], fill=base + (255,))

def build_bg(cw, ch, cx, cy, warp_grid=False, n_stars=1500):
    """Build the dark navy + grid + warp-stars bg at any canvas size."""
    bg = Image.new('RGBA', (cw, ch), DARK_NAVY + (255,))
    grid_draw = ImageDraw.Draw(bg)
    if warp_grid:
        draw_warp_grid(grid_draw, cw, ch, cx, cy)
    else:
        draw_orthogonal_grid(grid_draw, cw, ch, cx, cy)
    star_layer = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    draw_stars(star_layer, cw, ch, cx, cy, n_stars=n_stars)
    star_layer = star_layer.filter(ImageFilter.GaussianBlur(radius=0.6))
    return Image.alpha_composite(bg, star_layer)

# --- 2. Logo prep ---
logo = Image.open(LOGO).convert('RGBA')
LW, LH = logo.size
print(f'Logo source: {LW} x {LH} px (aspect {LW/LH:.3f})')

def fit_logo(avail_w, avail_h):
    scale = min(avail_w / LW, avail_h / LH)
    return round(LW * scale), round(LH * scale)

# Bordered logo size (sits inside the magenta frame)
b_w, b_h = fit_logo(W - 2 * BORDER - 2 * LOGO_PADDING, H - 2 * BORDER - 2 * LOGO_PADDING)
b_logo = logo.resize((b_w, b_h), Image.LANCZOS)
print(f'Bordered logo:  {b_w} x {b_h} px ({b_w/CM_TO_PX:.2f} x {b_h/CM_TO_PX:.2f} cm)')

# No-border logo size (1 cm top/bottom, 2 cm left/right padding)
NO_BORDER_PADDING_TB = round(1.0 * CM_TO_PX)
NO_BORDER_PADDING_LR = round(2.0 * CM_TO_PX)
nb_w, nb_h = fit_logo(W - 2 * NO_BORDER_PADDING_LR, H - 2 * NO_BORDER_PADDING_TB)
nb_logo = logo.resize((nb_w, nb_h), Image.LANCZOS)
print(f'No-border logo: {nb_w} x {nb_h} px ({nb_w/CM_TO_PX:.2f} x {nb_h/CM_TO_PX:.2f} cm)')

# --- 3. Variant builders ---
# Note on colour mode:
#   PIL's default RGB->CMYK is profile-less (no ICC, no proper black
#   extraction) and produces visibly duller colours than the source RGB.
#   We therefore keep the print PDFs in RGB. The print shop should convert
#   to CMYK at their end with their preferred ICC profile (FOGRA39,
#   ISO Coated v2, US SWOP, ...) which preserves the vivid colour intent
#   far better than a naive client-side conversion.
def save(image, key):
    png_name, pdf_name = OUT[key]
    rgb = image.convert('RGB')
    rgb.save(DIR / png_name, 'PNG', dpi=(DPI, DPI), optimize=True)
    rgb.save(DIR / pdf_name, 'PDF', resolution=DPI)
    sz_png = (DIR / png_name).stat().st_size / 1024
    sz_pdf = (DIR / pdf_name).stat().st_size / 1024
    print(f'  saved {png_name} ({sz_png:.0f} KB) + {pdf_name} ({sz_pdf:.0f} KB)')

def paint_magenta_frame(image, w, h, border_thickness):
    """Paint a solid magenta frame of `border_thickness` px on all 4 sides."""
    d = ImageDraw.Draw(image)
    d.rectangle([0, 0, w - 1, border_thickness - 1], fill=MAGENTA + (255,))
    d.rectangle([0, h - border_thickness, w - 1, h - 1], fill=MAGENTA + (255,))
    d.rectangle([0, 0, border_thickness - 1, h - 1], fill=MAGENTA + (255,))
    d.rectangle([w - border_thickness, 0, w - 1, h - 1], fill=MAGENTA + (255,))

# Trim-size canvases (54.5 x 11 cm) ---------------------------------
print('\nBuilding trim-size variants:')

bg_flat_trim = build_bg(W, H, W // 2, H // 2, warp_grid=False)
bg_warp_trim = build_bg(W, H, W // 2, H // 2, warp_grid=True)

# Bordered (trim)
img = bg_flat_trim.copy()
img.alpha_composite(b_logo, dest=((W - b_w) // 2, (H - b_h) // 2))
paint_magenta_frame(img, W, H, BORDER)
save(img, 'border')

# No-border flat (trim)
img = bg_flat_trim.copy()
img.alpha_composite(nb_logo, dest=((W - nb_w) // 2, (H - nb_h) // 2))
save(img, 'no-border')

# No-border warp (trim)
img = bg_warp_trim.copy()
img.alpha_composite(nb_logo, dest=((W - nb_w) // 2, (H - nb_h) // 2))
save(img, 'warp')

# Bleed-size canvases (55.1 x 11.6 cm) ------------------------------
# The trim area sits at offset (BLEED, BLEED) inside the bleed canvas.
# (cx, cy) of the bg is the bleed canvas centre, which equals the trim
# centre, so the star trails radiate from the same logical point.
print('\nBuilding bleed-size variants (3 mm afloop):')

bg_flat_bleed = build_bg(B_W, B_H, B_W // 2, B_H // 2, warp_grid=False)
bg_warp_bleed = build_bg(B_W, B_H, B_W // 2, B_H // 2, warp_grid=True)

# Bordered (bleed)
img = bg_flat_bleed.copy()
img.alpha_composite(b_logo, dest=((B_W - b_w) // 2, (B_H - b_h) // 2))
# Magenta frame: extends from bleed edges inward by BORDER + BLEED so that
# after the printer trims off the bleed strip, exactly BORDER (1.5 cm) of
# magenta is visible at the trim edge.
paint_magenta_frame(img, B_W, B_H, BORDER + BLEED)
save(img, 'border-bleed')

# No-border flat (bleed)
img = bg_flat_bleed.copy()
img.alpha_composite(nb_logo, dest=((B_W - nb_w) // 2, (B_H - nb_h) // 2))
save(img, 'no-border-bleed')

# No-border warp (bleed)
img = bg_warp_bleed.copy()
img.alpha_composite(nb_logo, dest=((B_W - nb_w) // 2, (B_H - nb_h) // 2))
save(img, 'warp-bleed')

print('\nDone.')
