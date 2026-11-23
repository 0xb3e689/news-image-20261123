#!/usr/bin/env python3
"""Generate the Monday 23 November 2026 world-news front-page HTML and render 1024x1024 PNG."""

import html
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
STORIES_PATH = os.path.join(ROOT, "stories.json")
OUT_PNG = os.path.join(ROOT, "assets", "entry.png")
TMP_HTML = "/tmp/news_20261123_v8.html"
TMP_QA300 = "/tmp/news_20261123_v8_300px.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

REGION_COLORS = {
    "EU": "#1E4D8C",
    "AM": "#6D28D9",
    "AS": "#047857",
    "AF": "#B45309",
    "ME": "#B91C1C",
    "OC": "#0F766E",
    "GL": "#334155",
}

STATUS_STYLES = {
    "CONFIRMED": ("#065F46", "#ECFDF5", "#059669"),
    "OFFICIAL": ("#1E3A8A", "#EFF6FF", "#2563EB"),
    "REPORTED": ("#92400E", "#FFFBEB", "#D97706"),
    "CLAIM": ("#991B1B", "#FEF2F2", "#DC2626"),
}

# Simplified real-world landmass polygons (lon, lat) in equirectangular projection
LAND_POLYGONS = [
    # North America
    [(-166, 65), (-155, 71), (-135, 69), (-110, 70), (-92, 63), (-82, 64), (-78, 53),
     (-64, 60), (-55, 52), (-60, 45), (-70, 42), (-76, 35), (-81, 25), (-83, 30),
     (-90, 29), (-97, 26), (-97, 19), (-88, 21), (-83, 15), (-78, 9), (-83, 8),
     (-92, 15), (-105, 20), (-110, 24), (-117, 32), (-124, 40), (-125, 49),
     (-136, 58), (-152, 60), (-163, 55)],
    # Greenland
    [(-52, 60), (-42, 60), (-22, 70), (-18, 81), (-40, 83), (-62, 76), (-55, 68)],
    # South America
    [(-78, 9), (-72, 12), (-61, 10), (-50, 2), (-35, -6), (-38, -14), (-41, -22),
     (-49, -28), (-55, -35), (-65, -42), (-68, -54), (-74, -52), (-73, -40),
     (-71, -18), (-81, -5), (-79, 2)],
    # Europe
    [(-9, 37), (-9, 43), (-2, 43), (-4, 48), (2, 51), (8, 54), (10, 58), (5, 61),
     (14, 68), (28, 71), (32, 69), (42, 66), (60, 68), (60, 50), (46, 46), (39, 45),
     (30, 46), (28, 41), (23, 37), (19, 40), (14, 45), (16, 40), (12, 41), (8, 44),
     (3, 43), (-1, 37), (-5, 36)],
    # UK & Ireland
    [(-6, 50), (-5, 58), (-1, 58), (2, 52), (-2, 50)],
    # Africa
    [(-17, 15), (-16, 21), (-9, 32), (-5, 36), (10, 37), (12, 33), (25, 32),
     (33, 31), (35, 25), (43, 12), (51, 12), (49, 5), (41, -2), (40, -11),
     (35, -20), (32, -26), (28, -33), (18, -34), (14, -22), (12, -6), (9, 4),
     (2, 6), (-8, 5), (-14, 10)],
    # Madagascar
    [(44, -25), (47, -25), (50, -15), (49, -12), (44, -18)],
    # Asia
    [(27, 41), (36, 37), (35, 31), (40, 20), (44, 13), (53, 16), (60, 22),
     (56, 26), (50, 29), (58, 25), (67, 25), (73, 19), (77, 8), (81, 16),
     (88, 22), (95, 16), (99, 13), (101, 2), (104, 2), (103, 13), (109, 12),
     (108, 21), (114, 22), (122, 31), (120, 39), (126, 35), (129, 36), (130, 42),
     (140, 48), (142, 55), (156, 59), (162, 60), (174, 65), (170, 70), (140, 73),
     (105, 76), (72, 72), (60, 68), (60, 50), (48, 45), (41, 41)],
    # Japan
    [(130, 32), (135, 34), (141, 36), (145, 44), (140, 42), (136, 37), (131, 34)],
    # Indonesia / Maritime SE Asia
    [(95, 5), (104, -1), (106, -6), (114, -8), (116, -8), (105, -5), (98, 2)],
    [(109, 1), (118, 5), (118, -3), (111, -3)],
    [(121, 18), (126, 8), (124, 6), (120, 14)],
    # Australia
    [(114, -22), (122, -17), (131, -12), (136, -12), (142, -11), (146, -19),
     (153, -27), (150, -37), (141, -38), (135, -34), (125, -33), (115, -34), (113, -26)],
    # New Zealand
    [(173, -35), (178, -38), (175, -41), (167, -46), (171, -43), (174, -39)],
]


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def proj(lon: float, lat: float, w: float = 248.0, h: float = 166.0):
    x = (lon + 180.0) / 360.0 * w
    # Crop latitudes from +80 to -58 for fuller vertical framing
    y = (80.0 - lat) / 138.0 * h
    return round(x, 1), round(y, 1)


def render_world_map(data: dict) -> str:
    w, h = 248.0, 166.0
    parts = [
        f'<svg viewBox="0 0 {int(w)} {int(h)}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{int(w)}" height="{int(h)}" fill="#D7E8F1" rx="3"/>',
    ]
    # Subtle latitude/longitude graticule
    for lat in (-30, 0, 30, 60):
        _, yy = proj(0, lat, w, h)
        parts.append(f'<line x1="0" y1="{yy}" x2="{int(w)}" y2="{yy}" stroke="#C3DAE6" stroke-width="0.6" stroke-dasharray="2,2"/>')
    for lon in (-120, -60, 0, 60, 120):
        xx, _ = proj(lon, 0, w, h)
        parts.append(f'<line x1="{xx}" y1="0" x2="{xx}" y2="{int(h)}" stroke="#C3DAE6" stroke-width="0.6" stroke-dasharray="2,2"/>')
    # Landmasses
    for poly in LAND_POLYGONS:
        pts = " ".join(f"{proj(lon, lat, w, h)[0]},{proj(lon, lat, w, h)[1]}" for lon, lat in poly)
        parts.append(f'<polygon points="{pts}" fill="#E6DEC8" stroke="#B7AD96" stroke-width="0.7" stroke-linejoin="round"/>')
    # Brief dots (#14-#50)
    for b in data["briefs"]:
        x, y = proj(b["lon"], b["lat"], w, h)
        col = REGION_COLORS[b["region"]]
        parts.append(f'<circle cx="{x}" cy="{y}" r="2.4" fill="{col}" opacity="0.76" stroke="#FAF8F3" stroke-width="0.5"/>')
    # Featured story numbered pins (#1-#13) with clean separation in Europe/Mid-East
    offsets = {
        1: (4, 0),
        2: (4, -3),
        4: (-7, 6),
        5: (3, 1),
        8: (-8, -6),
        10: (5, -8),
        13: (6, 2),
    }
    featured = data["heroes"] + data["features"]
    for st in featured:
        x, y = proj(st["lon"], st["lat"], w, h)
        dx, dy = offsets.get(st["id"], (0, 0))
        x = max(8.0, min(w - 8.0, x + dx))
        y = max(8.0, min(h - 8.0, y + dy))
        col = REGION_COLORS[st["region"]]
        r = 6.5 if st["id"] <= 3 else 5.6
        fs = 7.4 if st["id"] < 10 else 6.6
        parts.append(
            f'<g><circle cx="{x}" cy="{y}" r="{r}" fill="{col}" stroke="#FFFFFF" stroke-width="1.2"/>'
            f'<text x="{x}" y="{y + 2.5}" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,Arial,sans-serif" font-size="{fs}" font-weight="800">{st["id"]}</text></g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def hero_art(kind: str) -> str:
    if kind == "nvidia":
        return """<svg viewBox="0 0 326 88" width="100%" height="88" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="nvBg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0B1324"/><stop offset="100%" stop-color="#13253F"/>
    </linearGradient>
    <linearGradient id="nvArea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10B981" stop-opacity="0.45"/><stop offset="100%" stop-color="#10B981" stop-opacity="0.02"/>
    </linearGradient>
  </defs>
  <rect width="326" height="88" fill="url(#nvBg)"/>
  <g stroke="#243B5C" stroke-width="0.7">
    <line x1="0" y1="24" x2="214" y2="24"/><line x1="0" y1="46" x2="214" y2="46"/><line x1="0" y1="68" x2="214" y2="68"/>
  </g>
  <path d="M12,42 L48,54 L84,65 L112,72 L130,67 L148,46 L176,27 L204,16 L204,84 L12,84 Z" fill="url(#nvArea)"/>
  <polyline points="12,42 48,54 84,65 112,72" fill="none" stroke="#F87171" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="112,72 130,67 148,46 176,27 204,16" fill="none" stroke="#34D399" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="112" cy="72" r="3.5" fill="#F87171" stroke="#0B1324" stroke-width="1.2"/>
  <circle cx="204" cy="16" r="4.5" fill="#34D399" stroke="#FFFFFF" stroke-width="1.5"/>
  <text x="112" y="83" text-anchor="middle" fill="#FCA5A5" font-family="system-ui,sans-serif" font-size="7.4" font-weight="700">FRI $125.53</text>
  <rect x="7" y="6" width="164" height="16" rx="2" fill="#059669"/>
  <text x="89" y="17" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.2" font-weight="800">CEO REINSTATED · WALL ST RALLY</text>
  <rect x="216" y="6" width="103" height="76" rx="3" fill="#08101E" stroke="#2D4A6F" stroke-width="1"/>
  <text x="223" y="19" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="7.2" font-weight="700">MON 23 NOV CLOSE</text>
  <text x="223" y="36" fill="#34D399" font-family="system-ui,sans-serif" font-size="13.5" font-weight="900">+31.3%</text>
  <text x="312" y="35" text-anchor="end" fill="#E2E8F0" font-family="system-ui,sans-serif" font-size="8" font-weight="800">NVDA</text>
  <text x="223" y="45" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="7" font-weight="700">Close: $164.88</text>
  <line x1="223" y1="50" x2="312" y2="50" stroke="#1E3452" stroke-width="0.8"/>
  <text x="223" y="62" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="8.3" font-weight="700">S&amp;P 500</text>
  <text x="312" y="62" text-anchor="end" fill="#34D399" font-family="system-ui,sans-serif" font-size="8.8" font-weight="800">+4.73%</text>
  <text x="223" y="75" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="8.3" font-weight="700">NASDAQ</text>
  <text x="312" y="75" text-anchor="end" fill="#34D399" font-family="system-ui,sans-serif" font-size="8.8" font-weight="800">+6.5%</text>
</svg>"""
    if kind == "refinery":
        return """<svg viewBox="0 0 326 88" width="100%" height="88" xmlns="http://www.w3.org/2000/svg">
  <rect width="166" height="88" fill="#182234"/>
  <rect x="166" y="0" width="160" height="88" fill="#173854"/>
  <rect x="0" y="64" width="166" height="24" fill="#2A3447"/>
  <!-- Refinery towers -->
  <rect x="20" y="34" width="12" height="30" fill="#475569"/>
  <rect x="38" y="26" width="10" height="38" fill="#64748B"/>
  <rect x="54" y="42" width="24" height="22" fill="#334155"/>
  <rect x="84" y="30" width="11" height="34" fill="#475569"/>
  <rect x="102" y="45" width="26" height="19" fill="#334155"/>
  <!-- Flames & smoke -->
  <path d="M52,44 Q64,12 76,42 Q88,18 96,42 Z" fill="#EA580C"/>
  <path d="M58,44 Q66,22 74,43 Q82,27 89,44 Z" fill="#FACC15"/>
  <circle cx="70" cy="18" r="9" fill="#475569" opacity="0.65"/>
  <circle cx="84" cy="12" r="11" fill="#334155" opacity="0.55"/>
  <!-- Drone icon -->
  <path d="M126,22 L144,26 L126,30 L130,26 Z" fill="#E2E8F0"/>
  <line x1="112" y1="26" x2="124" y2="26" stroke="#F87171" stroke-width="1.2" stroke-dasharray="2,2"/>
  <rect x="6" y="6" width="114" height="15" rx="2" fill="#B91C1C"/>
  <text x="63" y="16.5" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.1" font-weight="800">PERM · 1,500 KM DEEP</text>
  <text x="8" y="80" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="7.7" font-weight="700">LUKOIL + NOVOSHAKHTINSK</text>
  <!-- Right panel: Libya naval strike -->
  <line x1="166" y1="0" x2="166" y2="88" stroke="#FAF8F3" stroke-width="2"/>
  <rect x="167" y="54" width="159" height="34" fill="#0F2942"/>
  <path d="M167,56 Q190,51 215,56 T265,56 T326,56" fill="none" stroke="#38BDF8" stroke-width="1.3" opacity="0.6"/>
  <!-- Capsizing corvette Merkury -->
  <g transform="translate(238,54) rotate(-18)">
    <polygon points="-36,0 34,0 26,12 -30,12" fill="#475569" stroke="#CBD5E1" stroke-width="0.9"/>
    <rect x="-14" y="-11" width="20" height="11" fill="#64748B"/>
    <line x1="-4" y1="-11" x2="-4" y2="-20" stroke="#CBD5E1" stroke-width="1.5"/>
  </g>
  <circle cx="242" cy="44" r="9" fill="#F97316" opacity="0.9"/>
  <circle cx="242" cy="44" r="4.5" fill="#FEF08A"/>
  <rect x="174" y="6" width="144" height="15" rx="2" fill="#1E4D8C"/>
  <text x="246" y="16.5" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.1" font-weight="800">BENGHAZI · CORVETTE SUNK</text>
  <text x="175" y="80" fill="#BAE6FD" font-family="system-ui,sans-serif" font-size="7.7" font-weight="700">MERKURY SUNK · MV ANGARA HIT</text>
</svg>"""
    return """<svg viewBox="0 0 326 88" width="100%" height="88" xmlns="http://www.w3.org/2000/svg">
  <rect width="326" height="88" fill="#E8D8BE"/>
  <!-- Nile confluence band -->
  <path d="M0,62 C65,58 115,44 162,48 C215,52 260,34 326,38 L326,52 C260,48 215,66 162,62 C115,58 65,72 0,76 Z" fill="#60A5FA" opacity="0.55"/>
  <!-- Khartoum buildings -->
  <rect x="12" y="38" width="32" height="30" fill="#B45309" opacity="0.82"/>
  <rect x="50" y="44" width="24" height="24" fill="#92400E" opacity="0.82"/>
  <!-- UN compound box (shifted left of starburst so text is 100% clear) -->
  <rect x="82" y="28" width="76" height="40" rx="2" fill="#FFFFFF" stroke="#0284C7" stroke-width="2"/>
  <rect x="82" y="28" width="76" height="14" fill="#0284C7"/>
  <text x="120" y="38" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.2" font-weight="900">UN COMPOUND</text>
  <rect x="96" y="48" width="14" height="12" fill="#BAE6FD"/>
  <rect x="128" y="48" width="14" height="12" fill="#BAE6FD"/>
  <!-- Impact burst cleanly at right roof edge -->
  <polygon points="168,26 174,17 177,26 186,23 180,31 187,38 177,36 174,45 170,36 160,37 166,31" fill="#DC2626"/>
  <circle cx="174" cy="31" r="4" fill="#FDE047"/>
  <!-- Right famine warning card -->
  <rect x="192" y="9" width="127" height="70" rx="3" fill="#7F1D1D"/>
  <text x="200" y="23" fill="#FCA5A5" font-family="system-ui,sans-serif" font-size="7.1" font-weight="800">WFP · UN SECURITY COUNCIL</text>
  <text x="200" y="40" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="11.5" font-weight="900">FAMINE RISK</text>
  <text x="200" y="54" fill="#FDE68A" font-family="system-ui,sans-serif" font-size="8.4" font-weight="800">SUDAN &amp; SOMALIA</text>
  <text x="200" y="68" fill="#FECACA" font-family="system-ui,sans-serif" font-size="7.4" font-weight="600">Triple trade chokepoint</text>
  <rect x="8" y="6" width="118" height="15" rx="2" fill="#B45309"/>
  <text x="67" y="16.5" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.1" font-weight="800">KHARTOUM DRONE HIT</text>
</svg>"""


def feature_art(kind: str) -> str:
    if kind == "spain":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#F1E9DA"/>
  <rect x="0" y="0" width="193" height="5" fill="#AA151B"/>
  <rect x="0" y="5" width="193" height="4" fill="#F1BF00"/>
  <!-- Scales of justice -->
  <line x1="36" y1="16" x2="36" y2="44" stroke="#1E3A8A" stroke-width="2.5"/>
  <line x1="18" y1="22" x2="54" y2="22" stroke="#1E3A8A" stroke-width="2.2"/>
  <path d="M18,22 L12,34 L24,34 Z" fill="none" stroke="#B45309" stroke-width="1.3"/>
  <path d="M54,22 L48,34 L60,34 Z" fill="none" stroke="#B45309" stroke-width="1.3"/>
  <rect x="26" y="44" width="20" height="3" fill="#1E3A8A"/>
  <!-- Stamp -->
  <rect x="74" y="16" width="108" height="24" rx="3" fill="#065F46"/>
  <text x="128" y="28" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="9.5" font-weight="900">AMNESTY</text>
  <text x="128" y="37" text-anchor="middle" fill="#A7F3D0" font-family="system-ui,sans-serif" font-size="7" font-weight="700">2017 CASE CLOSED</text>
</svg>"""
    if kind == "belgium":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#DCE8F2"/>
  <rect x="0" y="39" width="193" height="13" fill="#475569"/>
  <!-- Control tower -->
  <rect x="22" y="18" width="10" height="21" fill="#334155"/>
  <polygon points="16,18 38,18 34,10 20,10" fill="#1E293B"/>
  <rect x="19" y="12" width="16" height="4" fill="#38BDF8"/>
  <!-- Grounded plane -->
  <path d="M62,33 L96,33 L104,28 L108,28 L103,35 L62,35 Z" fill="#1E293B"/>
  <circle cx="84" cy="31" r="14" fill="none" stroke="#DC2626" stroke-width="2.6"/>
  <line x1="74" y1="21" x2="94" y2="41" stroke="#DC2626" stroke-width="2.6"/>
  <rect x="114" y="8" width="72" height="26" rx="2" fill="#B91C1C"/>
  <text x="150" y="20" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="9" font-weight="900">07–21h</text>
  <text x="150" y="30" text-anchor="middle" fill="#FECACA" font-family="system-ui,sans-serif" font-size="7.2" font-weight="800">ATC HALTED</text>
</svg>"""
    if kind == "drc":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#163038"/>
  <!-- Hospital block -->
  <rect x="14" y="14" width="52" height="32" rx="2" fill="#F8FAFC"/>
  <rect x="36" y="20" width="8" height="20" fill="#DC2626"/>
  <rect x="30" y="26" width="20" height="8" fill="#DC2626"/>
  <!-- Warning flashes -->
  <polygon points="72,16 79,23 73,26 81,34 71,30 74,23" fill="#F59E0B"/>
  <rect x="88" y="8" width="97" height="36" rx="3" fill="#991B1B"/>
  <text x="136.5" y="22" text-anchor="middle" fill="#FDE68A" font-family="system-ui,sans-serif" font-size="7.8" font-weight="800">ITURI · EBOLA ZONE</text>
  <text x="136.5" y="36" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="10" font-weight="900">WHO PEACE PLEA</text>
</svg>"""
    if kind == "asia_mkt":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#111827"/>
  <polyline points="8,10 28,13 46,22 66,18 84,33 98,27" fill="none" stroke="#EF4444" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="84" cy="33" r="2.8" fill="#EF4444"/>
  <text x="8" y="46" fill="#FCA5A5" font-family="system-ui,sans-serif" font-size="7.7" font-weight="800">KOSPI -3.3% (-5.8%)</text>
  <rect x="108" y="7" width="78" height="38" rx="3" fill="#047857"/>
  <text x="147" y="21" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.6" font-weight="900">TAIWAN BAN</text>
  <text x="147" y="32" text-anchor="middle" fill="#D1FAE5" font-family="system-ui,sans-serif" font-size="7.4" font-weight="700">NO SHORT SELL</text>
  <text x="147" y="41" text-anchor="middle" fill="#A7F3D0" font-family="system-ui,sans-serif" font-size="7" font-weight="700">150% MARGIN</text>
</svg>"""
    if kind == "fifa":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#14532D"/>
  <circle cx="96.5" cy="26" r="18" fill="none" stroke="#4ADE80" stroke-width="1" opacity="0.45"/>
  <line x1="96.5" y1="0" x2="96.5" y2="52" stroke="#4ADE80" stroke-width="1" opacity="0.45"/>
  <rect x="8" y="8" width="82" height="36" rx="3" fill="#0F172A" stroke="#FACC15" stroke-width="1.2"/>
  <text x="49" y="22" text-anchor="middle" fill="#FACC15" font-family="system-ui,sans-serif" font-size="11" font-weight="900">2031</text>
  <text x="49" y="34" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="7.4" font-weight="700">US·MX·CR·JM (48)</text>
  <rect x="103" y="8" width="82" height="36" rx="3" fill="#1E3A8A" stroke="#FACC15" stroke-width="1.2"/>
  <text x="144" y="22" text-anchor="middle" fill="#FACC15" font-family="system-ui,sans-serif" font-size="11" font-weight="900">2035</text>
  <text x="144" y="34" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="7.6" font-weight="800">UNITED KINGDOM</text>
</svg>"""
    if kind == "tajikistan":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#1E293B"/>
  <!-- Court columns -->
  <polygon points="14,17 62,17 38,8" fill="#CBD5E1"/>
  <rect x="18" y="19" width="6" height="22" fill="#94A3B8"/>
  <rect x="35" y="19" width="6" height="22" fill="#94A3B8"/>
  <rect x="52" y="19" width="6" height="22" fill="#94A3B8"/>
  <rect x="12" y="41" width="52" height="4" fill="#CBD5E1"/>
  <!-- Exit arrow -->
  <path d="M70,26 L92,26 L86,20 M92,26 L86,32" fill="none" stroke="#F87171" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="100" y="9" width="86" height="34" rx="3" fill="#B91C1C"/>
  <text x="143" y="23" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="9.5" font-weight="900">ICC EXIT</text>
  <text x="143" y="35" text-anchor="middle" fill="#FECACA" font-family="system-ui,sans-serif" font-size="7.4" font-weight="700">UN NOTIFIED · 2027</text>
</svg>"""
    if kind == "schools":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#E2E8F0"/>
  <!-- School building -->
  <polygon points="14,26 42,11 70,26" fill="#B91C1C"/>
  <rect x="18" y="26" width="48" height="20" fill="#FFFFFF" stroke="#64748B" stroke-width="1"/>
  <rect x="36" y="33" width="12" height="13" fill="#334155"/>
  <!-- Envelope alert -->
  <rect x="78" y="10" width="106" height="16" rx="2" fill="#1E293B"/>
  <text x="131" y="21" text-anchor="middle" fill="#FDE047" font-family="system-ui,sans-serif" font-size="7.8" font-weight="800">DK + DE · MASS EMAILS</text>
  <rect x="78" y="30" width="106" height="16" rx="2" fill="#065F46"/>
  <text x="131" y="41" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.2" font-weight="900">RULED HYBRID HOAX</text>
</svg>"""
    if kind == "cricket":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#166534"/>
  <rect x="0" y="36" width="193" height="16" fill="#CA8A04" opacity="0.35"/>
  <!-- Stumps -->
  <rect x="20" y="14" width="3" height="28" fill="#FDE68A"/>
  <rect x="27" y="14" width="3" height="28" fill="#FDE68A"/>
  <rect x="34" y="14" width="3" height="28" fill="#FDE68A"/>
  <rect x="19" y="12" width="19" height="2.5" fill="#F59E0B"/>
  <circle cx="54" cy="34" r="6" fill="#DC2626" stroke="#FFFFFF" stroke-width="1"/>
  <!-- Scoreboard -->
  <rect x="72" y="7" width="113" height="38" rx="3" fill="#0F172A"/>
  <text x="128.5" y="22" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="11.5" font-weight="900">NZ 239-5</text>
  <text x="128.5" y="34" text-anchor="middle" fill="#4ADE80" font-family="system-ui,sans-serif" font-size="7.8" font-weight="800">DAY 5 DRAW · 120 OV</text>
  <text x="128.5" y="42" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="6.8" font-weight="700">WELLINGTON 1ST TEST</text>
</svg>"""
    if kind == "indonesia":
        return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#27201C"/>
  <!-- Factory roofline -->
  <polygon points="8,46 8,28 24,20 24,28 40,20 40,28 60,28 60,46" fill="#44403C"/>
  <path d="M18,26 Q30,4 42,25 Q50,10 58,28 Z" fill="#EA580C"/>
  <path d="M24,27 Q32,12 40,27 Z" fill="#FACC15"/>
  <rect x="68" y="7" width="118" height="38" rx="3" fill="#991B1B"/>
  <text x="127" y="24" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="13" font-weight="900">24 DEAD</text>
  <text x="127" y="37" text-anchor="middle" fill="#FECACA" font-family="system-ui,sans-serif" font-size="7.2" font-weight="800">CIKANDE · DOZENS MISSING</text>
</svg>"""
    # israel
    return """<svg viewBox="0 0 193 52" width="100%" height="52" xmlns="http://www.w3.org/2000/svg">
  <rect width="193" height="52" fill="#EFF6FF"/>
  <rect x="0" y="0" width="193" height="5" fill="#1D4ED8"/>
  <rect x="0" y="47" width="193" height="5" fill="#1D4ED8"/>
  <rect x="10" y="10" width="76" height="32" rx="3" fill="#1E3A8A"/>
  <text x="48" y="24" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.6" font-weight="900">NO IRAN</text>
  <text x="48" y="35" text-anchor="middle" fill="#93C5FD" font-family="system-ui,sans-serif" font-size="8.2" font-weight="800">STRIKE NOW</text>
  <rect x="94" y="10" width="89" height="32" rx="3" fill="#B91C1C"/>
  <text x="138.5" y="24" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.4" font-weight="900">LIKUD TALKS</text>
  <text x="138.5" y="35" text-anchor="middle" fill="#FECACA" font-family="system-ui,sans-serif" font-size="8" font-weight="800">COLLAPSE</text>
</svg>"""


def status_pill(status: str) -> str:
    fg, bg, bd = STATUS_STYLES[status]
    return f'<span class="pill" style="color:{fg};background:{bg};border-color:{bd}">{esc(status)}</span>'


def build_html(data: dict) -> str:
    # UTC timeline items
    utc_items = "".join(
        f'<div class="utc-item"><span class="utc-t">{esc(u["time"])}</span><span class="utc-l">{esc(u["label"])}</span></div>'
        for u in data["utc_timeline"]
    )
    # Numbers strip
    num_items = "".join(
        f'<div class="num-item"><div class="num-v">{esc(n["val"])}</div><div class="num-l">{esc(n["label"])}</div></div>'
        for n in data["numbers"]
    )
    # Regional stacked bar
    reg_bars = "".join(
        f'<div class="reg-seg" style="flex:{r["count"]};background:{r["color"]}">{esc(r["name"])} {r["count"]}</div>'
        for r in data["region_counts"]
    )
    # Heroes (#1-#3)
    heroes_html = []
    for st in data["heroes"]:
        col = REGION_COLORS[st["region"]]
        heroes_html.append(
            f"""<article class="hero-card">
  <div class="hero-art">{hero_art(st["art"])}</div>
  <div class="card-meta">
    <span class="num-dot" style="background:{col}">{st["id"]}</span>
    <span class="kicker" style="color:{col}">{esc(st["kicker"])}</span>
    {status_pill(st["status"])}
  </div>
  <h2 class="hero-h">{esc(st["headline"])}</h2>
  <p class="hero-d">{esc(st["summary"])}</p>
  <div class="src">{esc(st["source"])}</div>
</article>"""
        )
    # Features (#4-#13)
    def render_feat_row(items):
        out = []
        for st in items:
            col = REGION_COLORS[st["region"]]
            out.append(
                f"""<article class="feat-card">
  <div class="feat-art">{feature_art(st["art"])}</div>
  <div class="card-meta">
    <span class="num-dot sm" style="background:{col}">{st["id"]}</span>
    <span class="kicker sm" style="color:{col}">{esc(st["kicker"])}</span>
    {status_pill(st["status"])}
  </div>
  <h3 class="feat-h">{esc(st["headline"])}</h3>
  <p class="feat-d">{esc(st["summary"])}</p>
  <div class="src sm">{esc(st["source"])}</div>
</article>"""
            )
        return "".join(out)

    feat_row1 = render_feat_row(data["features"][:5])
    feat_row2 = render_feat_row(data["features"][5:])

    # Briefs (#14-#50) split into 3 columns: 13 + 12 + 12
    briefs = data["briefs"]
    cols = [briefs[:13], briefs[13:25], briefs[25:]]
    brief_cols_html = []
    for col_items in cols:
        rows = []
        for b in col_items:
            col = REGION_COLORS[b["region"]]
            rows.append(
                f'<div class="b-row"><span class="b-num" style="background:{col}">{b["id"]}</span>'
                f'<div class="b-txt"><b>{esc(b["place"])}:</b> {esc(b["text"])} <span class="b-src">({esc(b["src"])})</span></div></div>'
            )
        brief_cols_html.append(f'<div class="b-col">{"".join(rows)}</div>')

    # Map region legend
    reg_legend = "".join(
        f'<span class="leg-item"><i style="background:{r["color"]}"></i>{esc(r["name"])} {r["count"]}</span>'
        for r in data["region_counts"]
    )

    world_svg = render_world_map(data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  width: 1024px; height: 1024px; overflow: hidden;
  background: #FAF8F2; color: #161614;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}}
.page {{
  width: 1024px; height: 1024px;
  padding: 7px 12px 6px 12px;
  display: flex; flex-direction: column; gap: 4px;
}}
.eyebrow {{
  display: flex; justify-content: space-between; align-items: center;
  font-size: 8.6px; font-weight: 800; letter-spacing: 0.4px;
  border-bottom: 1.5px solid #161614; padding-bottom: 2px;
}}
.eyebrow .left {{ color: #A61C1C; }}
.eyebrow .right {{ color: #334155; }}
.masthead {{
  text-align: center; padding: 0 0 3px 0;
  border-bottom: 2px solid #161614;
}}
.masthead h1 {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 44px; font-weight: 900; line-height: 0.98;
  letter-spacing: -0.6px; color: #111110;
}}
.masthead .sub {{
  font-family: Georgia, "Times New Roman", serif;
  font-style: italic; font-size: 10.6px; color: #3F3D36;
  margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.utc-bar {{
  display: flex; align-items: stretch; gap: 6px;
  background: #F1ECE0; border: 1px solid #D5CEBE; border-radius: 2px;
  padding: 2px 6px 2px 0;
}}
.utc-tag {{
  background: #A61C1C; color: #FFF; font-size: 7.4px; font-weight: 900;
  padding: 2px 6px; display: flex; align-items: center; text-align: center;
  line-height: 1.05; letter-spacing: 0.3px; flex-shrink: 0;
}}
.utc-items {{
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; flex: 1;
}}
.utc-item {{
  display: flex; flex-direction: column; align-items: center; text-align: center;
  border-left: 1px solid #D9D2C2; padding-left: 3px;
}}
.utc-item:first-child {{ border-left: none; padding-left: 0; }}
.utc-t {{ font-size: 8.4px; font-weight: 900; color: #A61C1C; line-height: 1.05; }}
.utc-l {{ font-size: 7.1px; font-weight: 600; color: #262522; line-height: 1.08; }}
.nums-row {{
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px;
  padding: 1px 0 2px 0;
}}
.num-item {{
  display: flex; align-items: baseline; gap: 5px;
  border-left: 1px solid #DDD6C7; padding-left: 6px;
}}
.num-item:first-child {{ border-left: none; padding-left: 2px; }}
.num-v {{
  font-family: Georgia, serif; font-size: 14.5px; font-weight: 900;
  color: #A61C1C; line-height: 1; white-space: nowrap;
}}
.num-l {{ font-size: 7.2px; color: #3B3934; line-height: 1.1; font-weight: 600; }}
.reg-bar {{
  display: flex; height: 13px; border-radius: 2px; overflow: hidden; gap: 1px;
}}
.reg-seg {{
  color: #FFF; font-size: 7.4px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  white-space: nowrap; letter-spacing: 0.2px;
}}
.heroes {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
}}
.hero-card {{
  display: flex; flex-direction: column; gap: 3px;
  border-bottom: 1.5px solid #161614; padding-bottom: 4px;
}}
.hero-art {{
  width: 100%; height: 88px; border: 1px solid #CFC8B8; border-radius: 2px; overflow: hidden;
}}
.card-meta {{
  display: flex; align-items: center; gap: 4px; margin-top: 1px;
}}
.num-dot {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 14px; height: 14px; border-radius: 50%;
  color: #FFF; font-size: 8.5px; font-weight: 900; flex-shrink: 0;
}}
.num-dot.sm {{ width: 12.5px; height: 12.5px; font-size: 7.5px; }}
.kicker {{
  font-size: 7.6px; font-weight: 800; letter-spacing: 0.25px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;
}}
.kicker.sm {{ font-size: 6.8px; }}
.pill {{
  font-size: 6.3px; font-weight: 800; padding: 0.5px 3.5px;
  border: 0.8px solid; border-radius: 2px; letter-spacing: 0.2px; flex-shrink: 0;
}}
.hero-h {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 13.8px; font-weight: 800; line-height: 1.13; color: #111110;
}}
.hero-d {{
  font-size: 8.5px; line-height: 1.24; color: #2D2C28;
}}
.src {{
  font-size: 7.2px; font-weight: 700; color: #646158; margin-top: auto;
}}
.src.sm {{ font-size: 6.6px; }}
.feats {{
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px;
}}
.feat-card {{
  display: flex; flex-direction: column; gap: 2px;
  border-bottom: 1px solid #D5CEBE; padding-bottom: 3px;
}}
.feat-art {{
  width: 100%; height: 52px; border: 1px solid #CFC8B8; border-radius: 2px; overflow: hidden;
}}
.feat-h {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 10.6px; font-weight: 800; line-height: 1.12; color: #111110;
}}
.feat-d {{
  font-size: 7.6px; line-height: 1.2; color: #31302B;
}}
.bottom-grid {{
  display: grid; grid-template-columns: 248px 1fr; gap: 10px;
  flex: 1; min-height: 0;
  border-top: 1.5px solid #161614; padding-top: 4px;
}}
.map-panel {{
  display: flex; flex-direction: column; gap: 4px;
}}
.sec-h {{
  font-size: 8.4px; font-weight: 900; letter-spacing: 0.4px;
  color: #A61C1C; text-transform: uppercase;
  display: flex; justify-content: space-between; align-items: baseline;
}}
.sec-h span {{ font-size: 7px; font-weight: 600; color: #57534A; text-transform: none; letter-spacing: 0; }}
.map-box {{
  width: 248px; height: 166px; border: 1px solid #C6BFAE; border-radius: 3px; overflow: hidden;
}}
.reg-leg {{
  display: flex; flex-wrap: wrap; gap: 3px 8px;
  font-size: 7.4px; font-weight: 700; color: #2D2C28;
  padding: 2px 0;
}}
.leg-item {{ display: inline-flex; align-items: center; gap: 3px; }}
.leg-item i {{ width: 7.5px; height: 7.5px; border-radius: 50%; display: inline-block; }}
.africa-strip {{
  background: #FEF3C7; border: 1px solid #D97706; border-radius: 2px;
  padding: 3.5px 6px; font-size: 7px; line-height: 1.24; color: #78350F;
}}
.africa-strip b {{ color: #92400E; }}
.sure-box {{
  background: #F2EDE1; border: 1px solid #D8D0C0; border-radius: 2px;
  padding: 4px 6px; margin-top: auto;
  font-size: 7.1px; line-height: 1.32; color: #2D2C28;
}}
.sure-box .sure-t {{ font-weight: 900; color: #161614; margin-bottom: 2px; font-size: 7.4px; }}
.briefs-panel {{
  display: flex; flex-direction: column; gap: 3px; min-height: 0;
}}
.b-cols {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
  flex: 1; min-height: 0;
}}
.b-col {{
  display: flex; flex-direction: column; justify-content: space-between;
  border-left: 1px solid #E2DCCD; padding-left: 6px;
}}
.b-col:first-child {{ border-left: none; padding-left: 0; }}
.b-row {{
  display: flex; align-items: flex-start; gap: 4px;
  font-size: 7.55px; line-height: 1.18; color: #1F1E1B;
}}
.b-num {{
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 13px; height: 13px; border-radius: 50%;
  color: #FFF; font-size: 6.7px; font-weight: 800; margin-top: 0.5px; flex-shrink: 0;
}}
.b-txt b {{ color: #111110; }}
.b-src {{ color: #6B665B; font-size: 6.7px; font-weight: 600; }}
.date-check {{
  display: flex; align-items: stretch; gap: 7px;
  border: 1.4px solid #A61C1C; background: #FDF6F5; border-radius: 2px;
  padding: 3px 7px 3px 0;
}}
.dc-tag {{
  background: #A61C1C; color: #FFF; font-size: 7.8px; font-weight: 900;
  padding: 3px 7px; display: flex; align-items: center; text-align: center;
  line-height: 1.1; flex-shrink: 0;
}}
.dc-body {{
  font-size: 7.25px; line-height: 1.24; color: #262320;
}}
.dc-body b {{ color: #7F1D1D; }}
.footer {{
  display: flex; justify-content: space-between; align-items: center;
  font-size: 7px; color: #57534A; font-weight: 600;
  border-top: 1px solid #D5CEBE; padding-top: 2px;
}}
</style>
</head>
<body>
<div class="page">
  <div class="eyebrow">
    <span class="left">{esc(data["eyebrow_left"])}</span>
    <span class="right">{esc(data["eyebrow_right"])}</span>
  </div>
  <header class="masthead">
    <h1>{esc(data["date_title"])}</h1>
    <div class="sub">{esc(data["subdeck"])}</div>
  </header>
  <section class="utc-bar">
    <div class="utc-tag">THE DAY<br>IN UTC</div>
    <div class="utc-items">{utc_items}</div>
  </section>
  <section class="nums-row">{num_items}</section>
  <section class="reg-bar">{reg_bars}</section>
  <section class="heroes">{"".join(heroes_html)}</section>
  <section class="feats">{feat_row1}</section>
  <section class="feats">{feat_row2}</section>
  <section class="bottom-grid">
    <div class="map-panel">
      <div class="sec-h">WHERE IT HAPPENED <span>pins #1–13 · dots #14–50</span></div>
      <div class="map-box">{world_svg}</div>
      <div class="reg-leg">{reg_legend}</div>
      <div class="africa-strip"><b>GLOBAL REACH:</b> 50 distinct stories across 35+ countries, including 8 African nations (Sudan, DRC, Senegal, Nigeria, Libya, Morocco, Ethiopia, South Africa).</div>
      <div class="sure-box">
        <div class="sure-t">HOW SURE (VERIFICATION KEY)</div>
        <div>{status_pill("CONFIRMED")} 2+ major outlets · {status_pill("OFFICIAL")} court, agency or result</div>
        <div style="margin-top:2px">{status_pill("REPORTED")} single major outlet · {status_pill("CLAIM")} one side's account</div>
      </div>
    </div>
    <div class="briefs-panel">
      <div class="sec-h">ALSO ON MONDAY 23 NOVEMBER — 37 MORE VERIFIED STORIES <span>numbered by region</span></div>
      <div class="b-cols">{"".join(brief_cols_html)}</div>
    </div>
  </section>
  <section class="date-check">
    <div class="dc-tag">DATE<br>CHECK</div>
    <div class="dc-body">
      <b>Audit:</b> {esc(data["date_check_left_out"])} <b>{esc(data["date_check_not_yet"])}</b>
    </div>
  </section>
  <footer class="footer">
    <span>Every story happened, or was first reported, on Monday 23 November 2026 (UTC/local). Claims attributed.</span>
    <span>Sources named beside each story · Original vector illustrations · 50 unique stories</span>
  </footer>
</div>
</body>
</html>
"""


def main() -> None:
    with open(STORIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    total = len(data["heroes"]) + len(data["features"]) + len(data["briefs"])
    if total != 50:
        raise ValueError(f"Expected 50 stories, got {total}")

    doc = build_html(data)
    with open(TMP_HTML, "w", encoding="utf-8") as f:
        f.write(doc)

    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--window-size=1024,1024",
        f"--screenshot={OUT_PNG}",
        f"file://{TMP_HTML}",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    from PIL import Image
    img = Image.open(OUT_PNG)
    w, h = img.size
    if (w, h) != (1024, 1024):
        raise RuntimeError(f"Unexpected dimensions: {w}x{h}")
    img.save(OUT_PNG, format="PNG", optimize=True)
    size_bytes = os.path.getsize(OUT_PNG)
    print(f"Rendered {OUT_PNG}: {w}x{h}, {size_bytes} bytes ({size_bytes/1024:.1f} KB)")
    if size_bytes > 1048576:
        raise RuntimeError(f"File too large: {size_bytes} bytes")
    qa = img.resize((300, 300), Image.Resampling.LANCZOS)
    qa.save(TMP_QA300)
    print(f"Saved 300px QA preview: {TMP_QA300}")


if __name__ == "__main__":
    main()
