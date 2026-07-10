#!/usr/bin/env python3
"""Generate the 1200x630 OG image for dateme.mhndlabs.com in the site's design language."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 630
BG = (12, 10, 10)          # --bg #0c0a0a
TEXT = (243, 235, 230)     # --text #f3ebe6
MUTED = (165, 152, 144)    # --muted #a59890
ACCENT = (255, 107, 107)   # --accent #ff6b6b
ACCENT_SOFT = (255, 176, 163)

img = Image.new("RGB", (W, H), BG)

# coral radial glow, top-right (matches the site's body::before)
glow = Image.new("RGB", (W, H), BG)
gd = ImageDraw.Draw(glow)
gd.ellipse([W - 520, -260, W + 260, 320], fill=(64, 26, 26))
glow = glow.filter(ImageFilter.GaussianBlur(160))
img = Image.blend(img, glow, 0.85)

d = ImageDraw.Draw(img)

def font(path, size):
    return ImageFont.truetype(path, size)

GEORGIA_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
GEORGIA_I = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
MENLO = "/System/Library/Fonts/Menlo.ttc"
HELV = "/System/Library/Fonts/Helvetica.ttc"

# eyebrow: mono, letterspaced, with leading rule (site's .eyebrow)
eyebrow = "O N - D E V I C E   D A T I N G - P H O T O   C O A C H"
f_eye = font(MENLO, 21)
d.line([(84, 118), (134, 118)], fill=ACCENT, width=2)
d.text((150, 106), eyebrow, font=f_eye, fill=ACCENT)

# headline: serif, two lines, italic accent word (site's h1)
f_h1 = font(GEORGIA_B, 88)
f_h1i = font(GEORGIA_I, 88)
d.text((80, 172), "Find the photo that", font=f_h1, fill=TEXT)
d.text((80, 278), "gets you ", font=f_h1, fill=TEXT)
w_prefix = d.textlength("gets you ", font=f_h1)
d.text((80 + w_prefix, 278), "matched.", font=f_h1i, fill=ACCENT_SOFT)

# lede
f_lede = font(HELV, 33)
d.text((84, 430), "Ranks your real photos, one fix each, bios in your voice —", font=f_lede, fill=MUTED)
d.text((84, 476), "all on your iPhone. No uploads. No AI faces.", font=f_lede, fill=MUTED)

# footer strip: brand + heart
f_brand = font(MENLO, 24)
d.text((84, 560), "♥", font=f_brand, fill=ACCENT)
d.text((116, 560), "DateMe", font=f_brand, fill=TEXT)
d.text((240, 560), "dateme.mhndlabs.com", font=f_brand, fill=MUTED)

# app icon, bottom right, rounded
try:
    icon = Image.open("app-icon.png").convert("RGBA").resize((120, 120), Image.LANCZOS)
    mask = Image.new("L", (120, 120), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 120, 120], radius=27, fill=255)
    img.paste(icon, (996, 486), mask)
except FileNotFoundError:
    pass

img.save("og.png", optimize=True)
print("og.png", img.size)
