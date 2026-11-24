#!/usr/bin/env python3
"""Generate the Monday 23 November 2026 world-news front-page HTML and render 1024x1024 PNG."""

import html
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
STORIES_PATH = os.path.join(ROOT, "stories.json")
OUT_PNG = os.path.join(ROOT, "assets", "entry.png")
TMP_HTML = "/tmp/news_20261123_v10.html"
TMP_QA300 = "/tmp/news_20261123_v10_300px.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

REGION_COLORS = {
    "EU": "#1E4D8C",
    "AS": "#047857",
    "AF": "#B45309",
    "AM": "#6D28D9",
    "ME": "#B91C1C",
    "OC": "#0F766E",
    "GL": "#334155",
}

STATUS_STYLES = {
    "OFFICIAL": ("#1E3A8A", "#EFF6FF", "#93C5FD"),
    "CONFIRMED": ("#065F46", "#ECFDF5", "#6EE7B7"),
    "REPORTED": ("#92400E", "#FFFBEB", "#FCD34D"),
    "CLAIM": ("#991B1B", "#FEF2F2", "#FCA5A5"),
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


def proj(lon: float, lat: float, w: float = 248.0, h: float = 160.0):
    x = (lon + 180.0) / 360.0 * w
    y = (80.0 - lat) / 138.0 * h
    return round(x, 1), round(y, 1)


def render_world_map(data: dict) -> str:
    w, h = 248.0, 160.0
    parts = [
        f'<svg viewBox="0 0 {int(w)} {int(h)}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{int(w)}" height="{int(h)}" fill="#D7E8F1" rx="3"/>',
    ]
    for lat in (-30, 0, 30, 60):
        _, yy = proj(0, lat, w, h)
        parts.append(f'<line x1="0" y1="{yy}" x2="{int(w)}" y2="{yy}" stroke="#C3DAE6" stroke-width="0.6" stroke-dasharray="2,2"/>')
    for lon in (-120, -60, 0, 60, 120):
        xx, _ = proj(lon, 0, w, h)
        parts.append(f'<line x1="{xx}" y1="0" x2="{xx}" y2="{int(h)}" stroke="#C3DAE6" stroke-width="0.6" stroke-dasharray="2,2"/>')
    for poly in LAND_POLYGONS:
        pts = " ".join(f"{proj(lon, lat, w, h)[0]},{proj(lon, lat, w, h)[1]}" for lon, lat in poly)
        parts.append(f'<polygon points="{pts}" fill="#E6DEC8" stroke="#B7AD96" stroke-width="0.7" stroke-linejoin="round"/>')
    for b in data["briefs"]:
        x, y = proj(b["lon"], b["lat"], w, h)
        col = REGION_COLORS[b["region"]]
        parts.append(f'<circle cx="{x}" cy="{y}" r="2.4" fill="{col}" opacity="0.76" stroke="#FAF8F3" stroke-width="0.5"/>')
    # Manual offsets so pins #1-#11 in Europe have clean separation
    offsets = {
        1: (4, 0),
        2: (5, -2),
        3: (7, -3),
        4: (-8, 8),
        5: (-10, 0),
        6: (0, 2),
        8: (-8, -12),
        9: (8, 7),
        10: (-2, 1),
    }
    for st in data["heroes"] + data["features"]:
        x, y = proj(st["lon"], st["lat"], w, h)
        dx, dy = offsets.get(st["id"], (0, 0))
        x = max(8.0, min(w - 8.0, x + dx))
        y = max(8.0, min(h - 8.0, y + dy))
        col = REGION_COLORS[st["region"]]
        r = 6.6 if st["id"] <= 3 else 5.8
        fs = 7.6 if st["id"] < 10 else 6.8
        parts.append(
            f'<g><circle cx="{x}" cy="{y}" r="{r}" fill="{col}" stroke="#FFFFFF" stroke-width="1.2"/>'
            f'<text x="{x}" y="{y + 2.6}" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,Arial,sans-serif" font-size="{fs}" font-weight="800">{st["id"]}</text></g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def hero_art(kind: str) -> str:
    if kind == "nvidia":
        return """<svg viewBox="0 0 326 96" width="100%" height="96" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="nvBg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0B1324"/><stop offset="100%" stop-color="#132641"/>
    </linearGradient>
    <linearGradient id="nvArea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10B981" stop-opacity="0.48"/><stop offset="100%" stop-color="#10B981" stop-opacity="0.02"/>
    </linearGradient>
  </defs>
  <rect width="326" height="96" fill="url(#nvBg)"/>
  <g stroke="#243B5C" stroke-width="0.7">
    <line x1="0" y1="26" x2="196" y2="26"/><line x1="0" y1="50" x2="196" y2="50"/><line x1="0" y1="74" x2="196" y2="74"/>
  </g>
  <path d="M10,46 L44,58 L76,69 L102,77 L120,71 L140,48 L166,27 L190,15 L190,92 L10,92 Z" fill="url(#nvArea)"/>
  <polyline points="10,46 44,58 76,69 102,77" fill="none" stroke="#F87171" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="102,77 120,71 140,48 166,27 190,15" fill="none" stroke="#34D399" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="102" cy="77" r="3.6" fill="#F87171" stroke="#0B1324" stroke-width="1.2"/>
  <circle cx="190" cy="15" r="4.8" fill="#34D399" stroke="#FFFFFF" stroke-width="1.6"/>
  <text x="102" y="90" text-anchor="middle" fill="#FCA5A5" font-family="system-ui,sans-serif" font-size="8.2" font-weight="800">FRI $125.53</text>
  <rect x="8" y="7" width="144" height="17" rx="2" fill="#059669"/>
  <text x="80" y="18.5" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.8" font-weight="900">JENSEN HUANG RETURNS</text>
  <rect x="200" y="7" width="119" height="82" rx="3" fill="#07101E" stroke="#2D4A6F" stroke-width="1"/>
  <text x="260" y="34" text-anchor="middle" fill="#34D399" font-family="system-ui,sans-serif" font-size="24" font-weight="900">+31.3%</text>
  <text x="260" y="48" text-anchor="middle" fill="#E2E8F0" font-family="system-ui,sans-serif" font-size="8.8" font-weight="800">NVDA $164.88</text>
  <line x1="210" y1="55" x2="309" y2="55" stroke="#1E3452" stroke-width="0.9"/>
  <text x="210" y="69" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="9" font-weight="700">S&amp;P 500</text>
  <text x="309" y="69" text-anchor="end" fill="#34D399" font-family="system-ui,sans-serif" font-size="9.6" font-weight="900">+4.73%</text>
  <text x="210" y="83" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="9" font-weight="700">NASDAQ</text>
  <text x="309" y="83" text-anchor="end" fill="#34D399" font-family="system-ui,sans-serif" font-size="9.6" font-weight="900">+6.5%</text>
</svg>"""
    if kind == "refinery":
        return """<svg viewBox="0 0 326 96" width="100%" height="96" xmlns="http://www.w3.org/2000/svg">
  <rect width="326" height="96" fill="#182334"/>
  <rect x="0" y="68" width="326" height="28" fill="#253145"/>
  <!-- Refinery towers -->
  <rect x="16" y="34" width="14" height="34" fill="#475569"/>
  <rect x="36" y="24" width="12" height="44" fill="#64748B"/>
  <rect x="54" y="42" width="28" height="26" fill="#334155"/>
  <rect x="88" y="30" width="13" height="38" fill="#475569"/>
  <rect x="108" y="46" width="30" height="22" fill="#334155"/>
  <!-- Bold flames -->
  <path d="M52,44 Q66,8 80,42 Q94,16 104,44 Z" fill="#EA580C"/>
  <path d="M59,44 Q68,20 77,43 Q86,26 95,44 Z" fill="#FACC15"/>
  <circle cx="74" cy="14" r="10" fill="#475569" opacity="0.6"/>
  <circle cx="92" cy="10" r="11" fill="#334155" opacity="0.5"/>
  <!-- Drone approaching -->
  <path d="M126,22 L148,27 L126,32 L131,27 Z" fill="#F8FAFC"/>
  <line x1="108" y1="27" x2="123" y2="27" stroke="#F87171" stroke-width="1.6" stroke-dasharray="3,2"/>
  <!-- Big focal figure block on right -->
  <text x="242" y="37" text-anchor="middle" fill="#FACC15" font-family="system-ui,sans-serif" font-size="25" font-weight="900">1,500 km</text>
  <text x="242" y="52" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="9.5" font-weight="800">PERM &amp; NOVOSHAKHTINSK</text>
  <rect x="162" y="60" width="156" height="20" rx="2" fill="#B91C1C"/>
  <text x="240" y="73.5" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.6" font-weight="900">UKRAINE CLAIMS BENGHAZI HIT</text>
  <text x="12" y="86" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="8.2" font-weight="800">LUKOIL REFINERY STRUCK</text>
</svg>"""
    return """<svg viewBox="0 0 326 96" width="100%" height="96" xmlns="http://www.w3.org/2000/svg">
  <rect width="326" height="96" fill="#DCE9F5"/>
  <rect x="0" y="68" width="326" height="28" fill="#334155"/>
  <line x1="16" y1="82" x2="310" y2="82" stroke="#CBD5E1" stroke-width="1.6" stroke-dasharray="10,8" opacity="0.6"/>
  <!-- ATC Control Tower -->
  <rect x="26" y="30" width="16" height="38" fill="#475569"/>
  <polygon points="16,30 52,30 46,16 22,16" fill="#1E293B"/>
  <rect x="21" y="20" width="26" height="6" fill="#38BDF8"/>
  <line x1="34" y1="6" x2="34" y2="16" stroke="#1E293B" stroke-width="2"/>
  <circle cx="34" cy="6" r="2.5" fill="#DC2626"/>
  <!-- Grounded plane with red prohibition sign -->
  <path d="M74,56 L128,56 L142,46 L149,46 L140,60 L74,60 Z" fill="#1E293B"/>
  <polygon points="94,56 108,42 115,42 106,56" fill="#475569"/>
  <circle cx="110" cy="52" r="22" fill="none" stroke="#DC2626" stroke-width="4.2"/>
  <line x1="94" y1="36" x2="126" y2="68" stroke="#DC2626" stroke-width="4.2"/>
  <!-- Huge stat callout -->
  <text x="242" y="38" text-anchor="middle" fill="#B91C1C" font-family="system-ui,sans-serif" font-size="28" font-weight="900">07–21h</text>
  <text x="242" y="53" text-anchor="middle" fill="#1E293B" font-family="system-ui,sans-serif" font-size="9.8" font-weight="900">ATC SHUTDOWN</text>
  <rect x="174" y="60" width="138" height="20" rx="2" fill="#1E293B"/>
  <text x="243" y="73.5" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="8.6" font-weight="800">BRUSSELS FLIGHTS HALTED</text>
</svg>"""


def feature_art(kind: str) -> str:
    if kind == "spain":
        return """<svg viewBox="0 0 242 56" width="100%" height="56" xmlns="http://www.w3.org/2000/svg">
  <rect width="242" height="56" fill="#F2EBD9"/>
  <rect width="242" height="5" fill="#AA151B"/>
  <rect y="5" width="242" height="4" fill="#F1BF00"/>
  <!-- Scales of justice -->
  <line x1="42" y1="16" x2="42" y2="47" stroke="#1E3A8A" stroke-width="2.8"/>
  <line x1="20" y1="23" x2="64" y2="23" stroke="#1E3A8A" stroke-width="2.4"/>
  <path d="M20,23 L13,37 L27,37 Z" fill="none" stroke="#B45309" stroke-width="1.6"/>
  <path d="M64,23 L57,37 L71,37 Z" fill="none" stroke="#B45309" stroke-width="1.6"/>
  <rect x="30" y="47" width="24" height="3.5" fill="#1E3A8A"/>
  <text x="158" y="33" text-anchor="middle" fill="#065F46" font-family="system-ui,sans-serif" font-size="22" font-weight="900">AMNESTY</text>
  <text x="158" y="47" text-anchor="middle" fill="#334155" font-family="system-ui,sans-serif" font-size="8.6" font-weight="800">2017 CATALAN CASE CLOSED</text>
</svg>"""
    if kind == "rohingya":
        return """<svg viewBox="0 0 242 56" width="100%" height="56" xmlns="http://www.w3.org/2000/svg">
  <rect width="242" height="56" fill="#EBF1F8"/>
  <!-- UK Union Jack mini badge -->
  <g transform="translate(10,8)">
    <rect width="34" height="20" fill="#012169" rx="1"/>
    <path d="M0,0 L34,20 M34,0 L0,20" stroke="#FFFFFF" stroke-width="4"/>
    <path d="M0,0 L34,20 M34,0 L0,20" stroke="#C8102E" stroke-width="1.8"/>
    <path d="M17,0 V20 M0,10 H34" stroke="#FFFFFF" stroke-width="6"/>
    <path d="M17,0 V20 M0,10 H34" stroke="#C8102E" stroke-width="3.2"/>
  </g>
  <!-- Sanctions document with red stamp -->
  <rect x="48" y="8" width="28" height="38" rx="2" fill="#FFFFFF" stroke="#64748B" stroke-width="1.1"/>
  <line x1="53" y1="16" x2="71" y2="16" stroke="#94A3B8" stroke-width="1.4"/>
  <line x1="53" y1="22" x2="71" y2="22" stroke="#94A3B8" stroke-width="1.4"/>
  <line x1="53" y1="28" x2="67" y2="28" stroke="#94A3B8" stroke-width="1.4"/>
  <circle cx="63" cy="37" r="6" fill="none" stroke="#B91C1C" stroke-width="1.8"/>
  <rect x="8" y="34" width="38" height="12" rx="1.5" fill="#166534"/>
  <text x="27" y="42.3" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="6.1" font-weight="800">COMMONS</text>
  <text x="160" y="30" text-anchor="middle" fill="#1E3A8A" font-family="system-ui,sans-serif" font-size="21" font-weight="900">5 GENERALS</text>
  <text x="160" y="45" text-anchor="middle" fill="#B91C1C" font-family="system-ui,sans-serif" font-size="8.4" font-weight="900">UK RECOGNISES GENOCIDE</text>
</svg>"""
    if kind == "nasa":
        return """<svg viewBox="0 0 242 56" width="100%" height="56" xmlns="http://www.w3.org/2000/svg">
  <rect width="242" height="56" fill="#0F172A"/>
  <!-- Lunar horizon + glowing fission core -->
  <ellipse cx="48" cy="56" rx="52" ry="18" fill="#64748B"/>
  <circle cx="48" cy="34" r="10" fill="#F59E0B" opacity="0.25"/>
  <rect x="42" y="26" width="12" height="16" rx="2" fill="#E2E8F0"/>
  <circle cx="48" cy="34" r="4" fill="#38BDF8"/>
  <circle cx="18" cy="14" r="1.4" fill="#F8FAFC"/><circle cx="78" cy="12" r="1.2" fill="#F8FAFC"/><circle cx="64" cy="20" r="1" fill="#94A3B8"/>
  <text x="164" y="32" text-anchor="middle" fill="#38BDF8" font-family="system-ui,sans-serif" font-size="24" font-weight="900">20 kW</text>
  <text x="164" y="46" text-anchor="middle" fill="#E2E8F0" font-family="system-ui,sans-serif" font-size="8.6" font-weight="800">LUNAR REACTOR-1 · 2030</text>
</svg>"""
    if kind == "asia_mkt":
        return """<svg viewBox="0 0 242 56" width="100%" height="56" xmlns="http://www.w3.org/2000/svg">
  <rect width="242" height="56" fill="#111827"/>
  <polyline points="10,12 34,16 54,28 74,23 94,43 110,34" fill="none" stroke="#EF4444" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="94" cy="43" r="3.5" fill="#EF4444"/>
  <text x="176" y="30" text-anchor="middle" fill="#F87171" font-family="system-ui,sans-serif" font-size="23" font-weight="900">-5.8%</text>
  <text x="176" y="45" text-anchor="middle" fill="#34D399" font-family="system-ui,sans-serif" font-size="8.4" font-weight="800">KOSPI LOW · TAIWAN BAN</text>
</svg>"""
    if kind == "nhs":
        return """<svg viewBox="0 0 242 56" width="100%" height="56" xmlns="http://www.w3.org/2000/svg">
  <rect width="242" height="56" fill="#E6F4F1"/>
  <!-- Radiology AI scan monitor -->
  <rect x="10" y="7" width="60" height="42" rx="3" fill="#0F172A" stroke="#0F766E" stroke-width="1.5"/>
  <g stroke="#1E3A5F" stroke-width="0.6">
    <line x1="25" y1="7" x2="25" y2="49"/><line x1="40" y1="7" x2="40" y2="49"/><line x1="55" y1="7" x2="55" y2="49"/>
    <line x1="10" y1="21" x2="70" y2="21"/><line x1="10" y1="35" x2="70" y2="35"/>
  </g>
  <ellipse cx="38" cy="29" rx="16" ry="12" fill="#334155" opacity="0.8"/>
  <circle cx="44" cy="25" r="7" fill="none" stroke="#22D3EE" stroke-width="1.8" stroke-dasharray="2.5,1.5"/>
  <circle cx="44" cy="25" r="2" fill="#22D3EE"/>
  <rect x="13" y="10" width="18" height="9" rx="1" fill="#0284C7"/>
  <text x="22" y="16.8" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="6.4" font-weight="900">NHS</text>
  <text x="158" y="31" text-anchor="middle" fill="#0F766E" font-family="system-ui,sans-serif" font-size="23.5" font-weight="900">700,000</text>
  <text x="158" y="45" text-anchor="middle" fill="#1E293B" font-family="system-ui,sans-serif" font-size="8.4" font-weight="800">WOMEN · £10M NHS AI TRIAL</text>
</svg>"""
    if kind == "fifa":
        return """<svg viewBox="0 0 242 56" width="100%" height="56" xmlns="http://www.w3.org/2000/svg">
  <rect width="242" height="56" fill="#14532D"/>
  <line x1="121" y1="0" x2="121" y2="56" stroke="#4ADE80" stroke-width="1.2" opacity="0.5"/>
  <circle cx="121" cy="28" r="14" fill="none" stroke="#4ADE80" stroke-width="1.2" opacity="0.45"/>
  <rect x="10" y="8" width="104" height="40" rx="3" fill="#0F172A" stroke="#FACC15" stroke-width="1.2"/>
  <text x="62" y="28" text-anchor="middle" fill="#FACC15" font-family="system-ui,sans-serif" font-size="18" font-weight="900">2031</text>
  <text x="62" y="41" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.2" font-weight="800">US·MX·CR·JM (48)</text>
  <rect x="128" y="8" width="104" height="40" rx="3" fill="#1E3A8A" stroke="#FACC15" stroke-width="1.2"/>
  <text x="180" y="28" text-anchor="middle" fill="#FACC15" font-family="system-ui,sans-serif" font-size="18" font-weight="900">2035</text>
  <text x="180" y="41" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.4" font-weight="800">UNITED KINGDOM</text>
</svg>"""
    if kind == "senegal":
        return """<svg viewBox="0 0 242 56" width="100%" height="56" xmlns="http://www.w3.org/2000/svg">
  <rect width="242" height="56" fill="#FEF3C7"/>
  <rect y="35" width="242" height="21" fill="#0369A1"/>
  <path d="M0,36 Q24,30 48,36 T96,36 T144,36" fill="none" stroke="#BAE6FD" stroke-width="1.8"/>
  <!-- Capsized pirogue hull -->
  <g transform="translate(52,35) rotate(-14)">
    <path d="M-28,0 Q0,-12 28,0 L22,6 L-22,6 Z" fill="#92400E" stroke="#451A03" stroke-width="1.2"/>
  </g>
  <text x="166" y="28" text-anchor="middle" fill="#9A3412" font-family="system-ui,sans-serif" font-size="24" font-weight="900">~100</text>
  <text x="166" y="48" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.4" font-weight="900">ABOARD · YENNE COAST</text>
</svg>"""
    # cricket
    return """<svg viewBox="0 0 242 56" width="100%" height="56" xmlns="http://www.w3.org/2000/svg">
  <rect width="242" height="56" fill="#E8F3E8"/>
  <rect x="0" y="42" width="242" height="14" fill="#166534"/>
  <!-- Stumps & ball -->
  <rect x="24" y="13" width="4" height="30" fill="#B45309"/>
  <rect x="33" y="13" width="4" height="30" fill="#B45309"/>
  <rect x="42" y="13" width="4" height="30" fill="#B45309"/>
  <rect x="23" y="11" width="24" height="3" fill="#D97706"/>
  <circle cx="64" cy="35" r="7" fill="#DC2626" stroke="#FFFFFF" stroke-width="1.2"/>
  <text x="160" y="32" text-anchor="middle" fill="#14532D" font-family="system-ui,sans-serif" font-size="25" font-weight="900">239-5</text>
  <text x="160" y="52" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="8.4" font-weight="800">DAY 5 DRAW · WELLINGTON</text>
</svg>"""


def status_tag(status: str) -> str:
    fg, bg, bd = STATUS_STYLES[status]
    return f'<span class="stag" style="color:{fg};background:{bg};border-color:{bd}">{esc(status)}</span>'


def build_html(data: dict) -> str:
    utc_items = "".join(
        f'<div class="utc-item"><span class="utc-t">{esc(u["time"])}</span><span class="utc-l">{esc(u["label"])}</span></div>'
        for u in data["utc_timeline"]
    )
    reg_bars = "".join(
        f'<div class="reg-seg" style="flex:{r["count"]};background:{r["color"]}">{esc(r["name"])} {r["count"]}</div>'
        for r in data["region_counts"]
    )
    heroes_html = []
    for st in data["heroes"]:
        col = REGION_COLORS[st["region"]]
        heroes_html.append(
            f"""<article class="hero-card">
  <div class="hero-art">{hero_art(st["art"])}</div>
  <div class="card-meta">
    <span class="num-dot" style="background:{col}">{st["id"]}</span>
    <span class="kicker" style="color:{col}">{esc(st["kicker"])}</span>
    {status_tag(st["status"])}
  </div>
  <h2 class="hero-h">{esc(st["headline"])}</h2>
  <p class="hero-d">{esc(st["summary"])}</p>
  <div class="src-foot">{esc(st["source"])}</div>
</article>"""
        )

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
    {status_tag(st["status"])}
  </div>
  <h3 class="feat-h">{esc(st["headline"])}</h3>
  <p class="feat-d">{esc(st["summary"])}</p>
  <div class="src-foot sm">{esc(st["source"])}</div>
</article>"""
            )
        return "".join(out)

    feat_row1 = render_feat_row(data["features"][:4])
    feat_row2 = render_feat_row(data["features"][4:])

    # 29 briefs split into 2 wide, ultra-readable columns: 15 left + 14 right
    briefs = data["briefs"]
    cols = [briefs[:15], briefs[15:]]
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

    reg_legend = "".join(
        f'<span class="leg-item"><i style="background:{r["color"]}"></i>{esc(r["name"])} {r["count"]}</span>'
        for r in data["region_counts"]
    )
    mkt_rows = "".join(
        f'<div class="m-row"><span class="m-name">{esc(m["name"])}</span>'
        f'<span class="m-val">{esc(m["val"])}</span>'
        f'<span class="m-chg {"up" if m["up"] else "dn"}">{esc(m["chg"])}</span></div>'
        for m in data["markets_close"]
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
  display: flex; flex-direction: column; gap: 4.5px;
}}
.eyebrow {{
  display: flex; justify-content: space-between; align-items: center;
  font-size: 8.8px; font-weight: 800; letter-spacing: 0.45px;
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
  font-size: 47px; font-weight: 900; line-height: 0.96;
  letter-spacing: -0.7px; color: #111110;
}}
.masthead .sub {{
  font-family: Georgia, "Times New Roman", serif;
  font-style: italic; font-size: 11px; color: #3F3D36;
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
.utc-t {{ font-size: 8.6px; font-weight: 900; color: #A61C1C; line-height: 1.05; }}
.utc-l {{ font-size: 7.2px; font-weight: 600; color: #262522; line-height: 1.08; }}
.reg-bar {{
  display: flex; height: 14px; border-radius: 2px; overflow: hidden; gap: 1px;
}}
.reg-seg {{
  color: #FFF; font-size: 7.6px; font-weight: 800;
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
.hero-art svg {{ height: 88px; }}
.card-meta {{
  display: flex; align-items: center; gap: 4px; margin-top: 1px;
}}
.num-dot {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 15px; height: 15px; border-radius: 50%;
  color: #FFF; font-size: 8.8px; font-weight: 900; flex-shrink: 0;
}}
.num-dot.sm {{ width: 13.5px; height: 13.5px; font-size: 7.8px; }}
.kicker {{
  font-size: 7.9px; font-weight: 800; letter-spacing: 0.25px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;
}}
.kicker.sm {{ font-size: 7.3px; }}
.stag {{
  font-size: 6.1px; font-weight: 800; padding: 0.5px 3.5px;
  border: 0.75px solid; border-radius: 2px; letter-spacing: 0.25px; flex-shrink: 0;
}}
.src-foot {{
  font-size: 7px; font-weight: 700; color: #646158; margin-top: auto;
}}
.src-foot.sm {{ font-size: 6.6px; }}
.hero-h {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 14.6px; font-weight: 800; line-height: 1.12; color: #111110;
}}
.hero-d {{
  font-size: 8.9px; line-height: 1.24; color: #2D2C28;
}}
.feats {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 9px;
}}
.feat-card {{
  display: flex; flex-direction: column; gap: 2.5px;
  border-bottom: 1px solid #D5CEBE; padding-bottom: 3.5px;
}}
.feat-art {{
  width: 100%; height: 52px; border: 1px solid #CFC8B8; border-radius: 2px; overflow: hidden;
}}
.feat-art svg {{ height: 52px; }}
.feat-h {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 11.7px; font-weight: 800; line-height: 1.12; color: #111110;
}}
.feat-d {{
  font-size: 8.1px; line-height: 1.22; color: #31302B;
}}
.bottom-grid {{
  display: grid; grid-template-columns: 248px 1fr; gap: 11px;
  flex: 1; min-height: 0;
  border-top: 1.5px solid #161614; padding-top: 4px;
}}
.map-panel {{
  display: flex; flex-direction: column; gap: 4px;
}}
.sec-h {{
  font-size: 8.5px; font-weight: 900; letter-spacing: 0.4px;
  color: #A61C1C; text-transform: uppercase;
  display: flex; justify-content: space-between; align-items: baseline;
}}
.sec-h span {{ font-size: 7.2px; font-weight: 600; color: #57534A; text-transform: none; letter-spacing: 0; }}
.map-box {{
  width: 248px; height: 160px; border: 1px solid #C6BFAE; border-radius: 3px; overflow: hidden;
}}
.reg-leg {{
  display: flex; flex-wrap: wrap; gap: 3px 8px;
  font-size: 7.4px; font-weight: 700; color: #2D2C28;
}}
.leg-item {{ display: inline-flex; align-items: center; gap: 3px; }}
.leg-item i {{ width: 7.5px; height: 7.5px; border-radius: 50%; display: inline-block; }}
.mkt-box {{
  background: #F2EDE1; border: 1px solid #D5CEBE; border-radius: 2px;
  padding: 5px 8px; margin-top: auto;
  display: flex; flex-direction: column; gap: 2.5px;
}}
.mkt-h {{
  font-size: 7.6px; font-weight: 900; color: #161614; letter-spacing: 0.35px;
  border-bottom: 1px solid #CFC8B8; padding-bottom: 2px; margin-bottom: 1.5px;
}}
.m-row {{
  display: grid; grid-template-columns: 1fr auto auto; gap: 6px; align-items: baseline;
  font-size: 7.6px; line-height: 1.24;
}}
.m-name {{ font-weight: 700; color: #1F1E1B; }}
.m-val {{ color: #57534A; font-weight: 600; font-size: 7.2px; }}
.m-chg {{ font-weight: 800; min-width: 41px; text-align: right; }}
.m-chg.up {{ color: #047857; }}
.m-chg.dn {{ color: #B91C1C; }}
.briefs-panel {{
  display: flex; flex-direction: column; gap: 3px; min-height: 0;
}}
.b-cols {{
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;
  flex: 1; min-height: 0;
}}
.b-col {{
  display: flex; flex-direction: column; justify-content: space-between;
  border-left: 1px solid #E2DCCD; padding-left: 8px;
}}
.b-col:first-child {{ border-left: none; padding-left: 0; }}
.b-row {{
  display: flex; align-items: flex-start; gap: 4.5px;
  font-size: 7.95px; line-height: 1.15; color: #1F1E1B;
}}
.b-num {{
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 14px; height: 14px; border-radius: 50%;
  color: #FFF; font-size: 7px; font-weight: 800; margin-top: 0.5px; flex-shrink: 0;
}}
.b-txt b {{ color: #111110; }}
.b-src {{ color: #6B665B; font-size: 7px; font-weight: 600; }}
.date-check {{
  display: flex; align-items: stretch; gap: 7px;
  border: 1.2px solid #A61C1C; background: #FDF7F6; border-radius: 2px;
  padding: 3px 7px 3px 0;
}}
.dc-tag {{
  background: #A61C1C; color: #FFF; font-size: 7.4px; font-weight: 900;
  padding: 2px 7px; display: flex; align-items: center; text-align: center;
  line-height: 1.1; flex-shrink: 0;
}}
.dc-body {{
  font-size: 7.1px; line-height: 1.22; color: #262320;
}}
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
  <section class="reg-bar">{reg_bars}</section>
  <section class="heroes">{"".join(heroes_html)}</section>
  <section class="feats">{feat_row1}</section>
  <section class="feats">{feat_row2}</section>
  <section class="bottom-grid">
    <div class="map-panel">
      <div class="sec-h">WHERE IT HAPPENED <span>pins #1–11 · dots #12–40</span></div>
      <div class="map-box">{world_svg}</div>
      <div class="reg-leg">{reg_legend}</div>
      <div class="mkt-box">
        <div class="mkt-h">MARKETS AT CLOSE · MON 23 NOV</div>
        {mkt_rows}
      </div>
    </div>
    <div class="briefs-panel">
      <div class="sec-h">ALSO ON MONDAY 23 NOVEMBER <span>29 more stories</span></div>
      <div class="b-cols">{"".join(brief_cols_html)}</div>
    </div>
  </section>
  <section class="date-check">
    <div class="dc-tag">DATE<br>CHECK</div>
    <div class="dc-body">{esc(data["date_check_text"])}</div>
  </section>
  <footer class="footer">
    <span>Monday 23 November 2026 · Claims attributed. {status_tag("OFFICIAL")} agency/court/result · {status_tag("CONFIRMED")} 2+ outlets · {status_tag("REPORTED")} 1 outlet</span>
    <span>Sources: Reuters, AP, BBC, Al Jazeera, Guardian, NASA, NHS, FIFA, WFP</span>
  </footer>
</div>
</body>
</html>
"""


def main() -> None:
    with open(STORIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    total = len(data["heroes"]) + len(data["features"]) + len(data["briefs"])
    if total != 40:
        raise ValueError(f"Expected 40 stories, got {total}")

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
