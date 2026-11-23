#!/usr/bin/env python3
# Generate newspaper front page - 40 stories, 23 Nov 2026
from PIL import Image, ImageDraw, ImageFont
import os, textwrap, json

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)) or '.', '..', 'assets', 'entry.png')

def load_font(size):
    for p in ['/System/Library/Fonts/Helvetica.ttc',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']:
        try: return ImageFont.truetype(p, size)
        except: pass
    return ImageFont.load_default()

BG = (248,245,238)
INK = (22,22,22)
RED = (178,42,42)
BLUE = (42,72,138)
OCHRE = (168,128,42)
GREEN = (52,118,62)
WHITE = (255,255,255)
GREY = (130,130,130)
BORDER = (198,193,183)
PANEL = (253,251,246)

img = Image.new('RGB', (W,H), BG)
d = ImageDraw.Draw(img)

# Masthead
MH = 90
d.rectangle([(0,0),(W,MH)], fill=INK)
d.line([(0,MH),(W,MH)], fill=RED, width=3)
d.text((30,15), 'WORLD NEWS', fill=WHITE, font=load_font(48))
d.text((30,58), 'MONDAY, 23 NOVEMBER 2026', fill=RED, font=load_font(22))

# Layout constants
G = 6  # gutter
GY = MH + G
GH = H - GY - G
CW = (W - 5*G) // 3  # column width
CH = (GH - 5*G) // 4  # card height (4 rows)

# Feature cards - 4 large cards in 2x2 grid (cols 0-1, rows 0-1)
# Small cards - 4 cards in col 2, rows 0-1 (2 per row)
# Headlines - col 2, rows 2-3

def card(x, y, w, h, color, tag, headline, source, tm, has_ill=False):
    d.rectangle([(x,y),(x+w,y+h)], fill=PANEL, outline=BORDER, width=1)
    d.rectangle([(x,y),(x+w,y+3)], fill=color)
    # tag
    d.text((x+6, y+6), tag, fill=color, font=load_font(12))
    # headline
    hl_font = load_font(15)
    lines = textwrap.wrap(headline, width=28)
    for j, ln in enumerate(lines[:3]):
        d.text((x+6, y+22+j*18), ln, fill=INK, font=hl_font)
    # source + time
    d.text((x+6, y+h-16), source + ' | ' + tm, fill=GREY, font=load_font(10))
    # simple illustration if has_ill
    if has_ill:
        cx, cy = x+w-40, y+h//2
        d.ellipse([(cx-18,cy-18),(cx+18,cy+18)], fill=color+(30,), outline=color, width=2)
# Stories: (tag, headline, source, time, color, lead)
S = [
    ('EUROPE | CLIMATE', 'COP31 Collapses as EU Rejects Fossil Fuel Omission', 'BBC', '07:23', RED, True),
    ('MIDDLE EAST | CONFLICT', 'Tankers Ablaze in Strait of Hormuz; IRGC Warns', 'Al Jazeera', '08:15', OCHRE, True),
    ('EUROPE | WAR', 'Russian Strike Kills Nine in Kyiv; Boy Rescued from Rubble', 'BBC', '11:40', BLUE, True),
    ('ASIA | MARKETS', 'Asian Stocks Tumble as AI Bubble Fears Mount Worldwide', 'Al Jazeera', '06:50', GREEN, True),
    ('ASIA | DISASTER', 'Indonesia Factory Fire Kills 3; Dozens Still Missing', 'BBC', '09:30', (88,98,112), False),
    ('AMERICAS | SECURITY', 'US Army Defies Court Order to Detonate Iowa Explosives', 'BBC', '14:05', INK, False),
    ('ASIA | POLITICS', 'South Korea Education Minister Resigns Over Exam Cheating', 'BBC', '05:15', BLUE, False),
    ('EUROPE | DIPLOMACY', 'UK PM Burnham Hails Landmark EU Deal as Path to Growth', 'BBC', '12:00', (100,80,40), False),
    ('EUROPE | SECURITY', 'Russia-Bound Ship Hit by Suspected Ukraine Drone in Gulf of Finland', 'BBC', '13:20', BLUE, False),
    ('AMERICAS | TECH', 'San Francisco AI Workers Fear Sector Overheating, Crash Looms', 'BBC', '11:15', GREEN, False),
    ('MIDDLE EAST | CONFLICT', 'Russian Navy Corvette Hit by Drone at Libya Port', 'Al Jazeera', '10:45', OCHRE, False),
    ('AMERICAS | SOCIETY', '9 People Shot at Central California Concert; 1 Critical', 'AP', '08:45', RED, False),
    ('AMERICAS | POLITICS', 'Democrats Win Largest House Majority Since 1992, Flipping NC', 'BBC', '03:30', BLUE, False),
    ('MIDDLE EAST | DIPLOMACY', 'Netanyahu Coalition Talks Fail; Eisenkot Deal Unreached', 'Al Jazeera', '14:30', OCHRE, False),
    ('AMERICAS | POLITICS', 'Trump Criticises Schumer Amid Push for New Democrat Leadership', 'Al Jazeera', '07:55', INK, False),
    ('AMERICAS | DIPLOMACY', 'US Intelligence Chief Defends Trump Calling Putin His Friend', 'Al Jazeera', '08:40', INK, False),
    ('AFRICA | CONFLICT', 'Sudan Displaced Families Face Volatile Winter as Aid Cuts Bite', 'Al Jazeera', '06:10', OCHRE, False),
    ('AFRICA | SOCIETY', 'Cameroon Ex-Rebels Caught Between Hiding and Broken Promises', 'Al Jazeera', '05:50', GREEN, False),
    ('AMERICAS | CRIME', 'El Chapo Isidro, Alleged Mexican Cartel Leader, Captured', 'Al Jazeera', '11:25', RED, False),
    ('ASIA | POLITICS', 'Kenya Internet Metering Bill Raises Privacy, Affordability Concerns', 'Al Jazeera', '06:35', BLUE, False),
    ('AMERICAS | CLIMATE', 'Haiti Farmers Rebuild Amid Violence, Hunger and El Nino', 'AP', '09:20', GREEN, False),
    ('EUROPE | SPORT', 'Alcaraz Outplays Zverev for First ATP Finals Triumph in Turin', 'BBC', '16:00', (100,40,120), False),
    ('EUROPE | SPORT', 'FIFA Confirms UK as Host for 2035 Women World Cup', 'BBC', '11:30', (100,40,120), False),
    ('AMERICAS | SPORT', 'Verstappen Star Figure in Chaotic Las Vegas Grand Prix', 'BBC', '15:30', (100,40,120), False),
    ('EUROPE | SPORT', 'Man United Endure Chaotic Week Under New Boss Pochettino', 'BBC', '14:45', (100,40,120), False),
    ('AMERICAS | SOCIETY', 'Miley Cyrus Marries Maxx Morando in California Ceremony', 'BBC', '15:10', (180,60,100), False),
    ('ASIA | SOCIETY', 'Australian Music Legend Molly Meldrum Dies Aged 83', 'BBC', '14:50', INK, False),
    ('EUROPE | SOCIETY', 'Italian Jeweller Paolo Bulgari Dies Aged 89', 'BBC', '13:40', INK, False),
    ('AMERICAS | SOCIETY', 'Seattle Airport Outraged Over ICE Arrest of Two Passengers', 'BBC', '10:30', BLUE, False),
    ('EUROPE | HEALTH', 'NHS Launches World Largest AI Breast Cancer Detection Trial', 'BBC', '09:15', GREEN, False),
    ('AMERICAS | SCIENCE', 'US Declassifies More UFO Footage Filmed in Middle East', 'BBC', '12:50', BLUE, False),
    ('ASIA | SPORT', 'Gukesh vs Sindarov: Youngest World Chess Championship in History', 'Al Jazeera', '10:00', (100,40,120), False),
    ('AMERICAS | MARKETS', 'Anthropic IPO Greenshoe Exercised at $93.5 Billion Total', 'Reuters', '16:30', GREEN, False),
    ('EUROPE | TECH', 'Germany IT Security Threat Level Raised to Critical Over AI Attacks', 'Reuters', '06:00', RED, False),
    ('ASIA | MARKETS', 'Australia Services PMI Falls to 46.2, Deepening Contraction', 'Forex News', '02:00', GREEN, False),
    ('EUROPE | SOCIETY', 'Russell Brand Wife to Honour Prison Rules After Message Row', 'BBC', '13:10', INK, False),
    ('AMERICAS | SOCIETY', 'Argentina Paredes Collapses During Post-Match TV Interview', 'BBC', '04:00', RED, False),
    ('MIDDLE EAST | HEALTH', 'Gaza Children Struggle to Find Life-Saving Insulin for Diabetes', 'Al Jazeera', '07:40', RED, False),
    ('EUROPE | SPORT', 'Gerwyn Price Wins Grand Slam of Darts to End Four-Year Drought', 'BBC', '17:00', (100,40,120), False),
]
# Layout: 4 big leads in 2x2, then 4-col headline grid below
leads = [s for s in S if s[5]]
rest = [s for s in S if not s[5]]
# Top: 4 lead cards with larger text
for i, s in enumerate(leads[:4]):
    r, c = i // 2, i % 2
    x = G + c*(CW+G)
    y = GY + r*(CH+G)
    color = s[4]
    d.rectangle([(x,y),(x+CW,y+CH)], fill=PANEL, outline=BORDER, width=1)
    d.rectangle([(x,y),(x+CW,y+3)], fill=color)
    d.text((x+8, y+7), s[0], fill=color, font=load_font(14))
    for j, ln in enumerate(textwrap.wrap(s[1], width=24)[:3]):
        d.text((x+8, y+28+j*24), ln, fill=INK, font=load_font(20))
    d.text((x+8, y+CH-16), f'{s[2]} | {s[3]}', fill=GREY, font=load_font(11))
    cx, cy = x+CW-42, y+CH//2
    d.ellipse([(cx-20,cy-20),(cx+20,cy+20)], fill=color+(35,), outline=color, width=2)
# Bottom: 4-col headline grid
HL_Y = GY + 2*(CH+G)
HL_H = H - HL_Y - G
hl_rows = 9
row_h = HL_H // hl_rows
for i, s in enumerate(rest):
    col = i // hl_rows
    row = i % hl_rows
    px = G + col*(CW+G) + 4
    py = HL_Y + row*row_h + 2
    tag = s[0].split('|')[0].strip()[:16]
    d.text((px, py), f'{tag}  {s[1][:58]}', fill=INK, font=load_font(13))
    d.text((px, py+12), f'{s[2]}  {s[3]}', fill=GREY, font=load_font(10))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, 'PNG', optimize=True)
print(f'Saved {OUT} ({W}x{H}), {os.path.getsize(OUT)} bytes')