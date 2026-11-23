#!/usr/bin/env python3
"""Generate editorial news image for 23 November 2026."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", "..", "assets", "entry.png")

# Colors
BG = (247, 244, 236)
INK = (20, 20, 20)
RED = (180, 45, 45)
BLUE = (45, 75, 140)
OCHRE = (170, 130, 45)
GREEN = (55, 120, 65)
SLATE = (90, 100, 115)
WHITE = (255, 255, 255)
BORDER = (200, 195, 185)
PANEL_BG = (252, 250, 245)

# Fonts
def load_font(size, bold=False):
    paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Times.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()

font_title = load_font(52, bold=True)
font_date = load_font(26, bold=True)
font_headline = load_font(27, bold=True)
font_headline_sm = load_font(22, bold=True)
font_tag = load_font(17, bold=True)
font_tag_sm = load_font(14, bold=True)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

MASTHEAD_H = 120

# Masthead background
draw.rectangle([(0, 0), (W, MASTHEAD_H)], fill=INK)
draw.line([(0, MASTHEAD_H), (W, MASTHEAD_H)], fill=RED, width=4)

# Title and date in masthead
draw.text((40, 22), "WORLD NEWS", fill=WHITE, font=font_title)
draw.text((40, 78), "MONDAY, 23 NOVEMBER 2026", fill=RED, font=font_date)

# Grid area
GY = MASTHEAD_H + 12
GH = H - GY - 12
GUTTER = 10

# Lead panel (left half)
lead_w = (W - 3 * GUTTER) // 2
lead_h = GH
lead_x = GUTTER
lead_y = GY

# Secondary panels (right half, 2 cols x 3 rows)
sec_x = lead_x + lead_w + GUTTER
sec_w = W - sec_x - GUTTER
sec_col_w = (sec_w - GUTTER) // 2
sec_rows = 3
sec_row_h = (GH - 2 * GUTTER) // sec_rows

def draw_panel(x, y, w, h, tag, headline, accent_color, story_idx, is_lead=False):
    draw.rectangle([(x, y), (x + w, y + h)], fill=PANEL_BG, outline=BORDER, width=1)
    draw.rectangle([(x, y), (x + w, y + 4)], fill=accent_color)
    tag_font = font_tag if is_lead else font_tag_sm
    draw.text((x + 10, y + 10), tag, fill=accent_color, font=tag_font)
    hl_font = font_headline if is_lead else font_headline_sm
    headline_y = y + (50 if is_lead else 34)
    ill_h = h - (120 if is_lead else 70)
    ill_y = y + (90 if is_lead else 60)
    cx, cy = x + w // 2, ill_y + (y + h - 12 - ill_y) // 2
    r = min(w, y + h - 12 - ill_y) // 3
    # Draw simple editorial illustration based on story index
    draw_illustration(x + 12, ill_y, w - 24, y + h - 12 - ill_y, story_idx, accent_color)
    words = headline.split()
    mid = len(words) // 2 + (1 if len(words) % 2 else 0)
    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:]) if len(words) > mid else ""
    draw.text((x + 10, headline_y), line1, fill=INK, font=hl_font)
    if line2:
        draw.text((x + 10, headline_y + hl_font.size + 4), line2, fill=INK, font=hl_font)

def draw_illustration(x, y, w, h, idx, color):
    r, g, b = color
    light = (min(255, r + 100), min(255, g + 100), min(255, b + 100))
    mid = (r // 2, g // 2, b // 2)
    cx, cy = x + w // 2, y + h // 2
    if idx == 0:  # COP31 - globe/sphere
        draw.ellipse([(cx - w // 3, cy - h // 3), (cx + w // 3, cy + h // 3)], fill=light, outline=color, width=3)
        draw.arc([(cx - w // 4, cy - h // 4), (cx + w // 4, cy + h // 4)], 0, 180, fill=color, width=2)
        draw.line([(cx - w // 3, cy), (cx + w // 3, cy)], fill=color, width=2)
    elif idx == 1:  # Tanker/Hormuz - ship silhouette
        ship_y = cy + h // 8
        draw.polygon([(cx - w // 3, ship_y), (cx - w // 4, cy - h // 5), (cx + w // 4, cy - h // 5), (cx + w // 3, ship_y)], fill=light, outline=color, width=2)
        draw.rectangle([(cx - w // 12, cy - h // 5 - h // 8), (cx + w // 12, cy - h // 5)], fill=color)
    elif idx == 2:  # Kyiv war - damaged building + rescue
        bldg_w, bldg_h = w // 2, h // 2
        draw.rectangle([(cx - bldg_w // 2, y + h // 4), (cx + bldg_w // 2, y + h // 4 + bldg_h)], fill=light, outline=color, width=2)
        draw.polygon([(cx - bldg_w // 2 - 8, y + h // 4), (cx, y + h // 8), (cx + bldg_w // 2 + 8, y + h // 4)], fill=color, outline=color, width=1)
        draw.line([(cx, y + h // 4), (cx, cy + h // 4)], fill=color, width=2)
    elif idx == 3:  # Markets/AI - downward arrow + circuit
        draw.line([(cx - w // 4, cy + h // 4), (cx, cy - h // 4), (cx + w // 4, cy + h // 4)], fill=color, width=4)
        draw.line([(cx + w // 4, cy + h // 4), (cx + w // 4 + 15, cy + h // 4 - 10)], fill=color, width=4)
        draw.line([(cx + w // 4, cy + h // 4), (cx + w // 4 + 15, cy + h // 4 + 10)], fill=color, width=4)
    elif idx == 4:  # Factory fire - flames
        for i in range(3):
            fx = cx - w // 6 + i * w // 6
            fy = y + h // 2
            fw, fh = w // 8, h // 3
            draw.ellipse([(fx - fw, fy), (fx + fw, fy - fh)], fill=light, outline=color, width=2)
    elif idx == 5:  # Iowa explosives - warning triangle
        draw.polygon([(cx, cy - h // 3), (cx - w // 3, cy + h // 3), (cx + w // 3, cy + h // 3)], fill=light, outline=color, width=3)
        draw.text((cx - 15, cy - 8), "!", fill=color, font=font_headline)

# Stories for 23 November 2026
stories = [
    # (tag, headline, color, is_lead)
    ("EUROPE \u00b7 CLIMATE", "COP31 Collapses as EU Rejects Fossil Fuel Omission", RED, True),
    ("MIDDLE EAST \u00b7 CONFLICT", "Tankers Ablaze in Hormuz as IRGC Warns of Unrest", OCHRE, False),
    ("EUROPE \u00b7 WAR", "Russian Strike Kills Nine in Kyiv; Boy Rescued", BLUE, False),
    ("ASIA \u00b7 MARKETS", "Asian Markets Tumble on Mounting AI Bubble Fears", GREEN, False),
    ("ASIA \u00b7 DISASTER", "Indonesia Factory Fire Kills Three, Dozens Missing", SLATE, False),
    ("AMERICAS \u00b7 SECURITY", "US Army Defies Court to Detonate Iowa Explosives", INK, False),
]

# Draw lead panel
lead_story = stories[0]
draw_panel(lead_x, lead_y, lead_w, lead_h, lead_story[0], lead_story[1], lead_story[2], is_lead=True)

# Draw secondary panels
for i, story in enumerate(stories[1:]):
    row = i // 2
    col = i % 2
    px = sec_x + col * (sec_col_w + GUTTER)
    py = GY + row * (sec_row_h + GUTTER)
    draw_panel(px, py, sec_col_w, sec_row_h, story[0], story[1], story[2], is_lead=False)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, "PNG", optimize=True)
print(f"Saved {OUT}  ({W}x{H})")
sz = os.path.getsize(OUT)
print(f"Size: {sz} bytes ({sz/1024:.1f} KB)")
assert sz <= 1048576, f"Over 1 MiB limit: {sz}"
print("OK")