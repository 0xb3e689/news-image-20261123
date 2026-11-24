#!/usr/bin/env python3
"""Generate the Monday 23 November 2026 world-news front-page HTML and render 1024x1024 PNG."""

import html
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
STORIES_PATH = os.path.join(ROOT, "stories.json")
OUT_PNG = os.path.join(ROOT, "assets", "entry.png")
TMP_HTML = "/tmp/news_20261123_v11.html"
TMP_QA300 = "/tmp/news_20261123_v11_300px.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

REGION_COLORS = {
    "EU": "#1E4D8C",
    "AS": "#047857",
    "AF": "#B45309",
    "ME": "#B91C1C",
    "AM": "#6D28D9",
    "OC": "#0F766E",
    "GL": "#334155",
}

STATUS_BADGE = {
    "OFFICIAL": ("#FFFFFF", "#1E4D8C"),
    "CONFIRMED": ("#FFFFFF", "#047857"),
    "REPORTED": ("#FFFFFF", "#B45309"),
    "CLAIM": ("#FFFFFF", "#B91C1C"),
}

# Simplified Natural-Earth landmass polygons (lon, lat)
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


def proj(lon: float, lat: float, w: float = 248.0, h: float = 196.0):
    x = (lon + 180.0) / 360.0 * w
    y = (80.0 - lat) / 138.0 * h
    return round(x, 1), round(y, 1)


def render_world_map(data: dict) -> str:
    w, h = 248.0, 196.0
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
        parts.append(f'<circle cx="{x}" cy="{y}" r="2.2" fill="{col}" opacity="0.72" stroke="#FAF8F3" stroke-width="0.5"/>')
    offsets = {
        1: (4, 0),
        2: (5, -2),
        3: (6, -3),
        4: (-8, 8),
        5: (-10, 0),
        6: (0, 2),
        8: (-8, -12),
        9: (8, 7),
        10: (0, 2),
        11: (-2, 1),
        12: (3, 1),
    }
    for st in data["heroes"] + data["features"]:
        x, y = proj(st["lon"], st["lat"], w, h)
        dx, dy = offsets.get(st["id"], (0, 0))
        x = max(8.0, min(w - 8.0, x + dx))
        y = max(8.0, min(h - 8.0, y + dy))
        col = REGION_COLORS[st["region"]]
        r = 6.2 if st["id"] <= 3 else 5.5
        fs = 7.2 if st["id"] < 10 else 6.4
        parts.append(
            f'<g><circle cx="{x}" cy="{y}" r="{r}" fill="{col}" stroke="#FFFFFF" stroke-width="1.15"/>'
            f'<text x="{x}" y="{y + 2.4}" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,Arial,sans-serif" font-size="{fs}" font-weight="800">{st["id"]}</text></g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def hero_art(kind: str) -> str:
    if kind == "nvidia":
        return """<svg viewBox="0 0 264 88" width="100%" height="88" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="nvBg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0B1324"/><stop offset="100%" stop-color="#132944"/>
    </linearGradient>
    <linearGradient id="nvArea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10B981" stop-opacity="0.45"/><stop offset="100%" stop-color="#10B981" stop-opacity="0.02"/>
    </linearGradient>
  </defs>
  <rect width="264" height="88" fill="url(#nvBg)"/>
  <g stroke="#243B5C" stroke-width="0.6">
    <line x1="0" y1="24" x2="264" y2="24"/><line x1="0" y1="48" x2="264" y2="48"/><line x1="0" y1="70" x2="264" y2="70"/>
  </g>
  <path d="M8,44 L36,54 L66,64 L90,72 L106,66 L124,44 L148,26 L172,16 L172,84 L8,84 Z" fill="url(#nvArea)"/>
  <polyline points="8,44 36,54 66,64 90,72" fill="none" stroke="#F87171" stroke-width="2.8" stroke-linecap="round"/>
  <polyline points="90,72 106,66 124,44 148,26 172,16" fill="none" stroke="#34D399" stroke-width="3.4" stroke-linecap="round"/>
  <circle cx="90" cy="72" r="3.2" fill="#F87171"/>
  <circle cx="172" cy="16" r="4.2" fill="#34D399" stroke="#FFFFFF" stroke-width="1.4"/>
  <text x="90" y="83" text-anchor="middle" fill="#FCA5A5" font-family="system-ui,sans-serif" font-size="7.4" font-weight="800">FRI $125.53</text>
  <rect x="178" y="8" width="80" height="54" rx="3" fill="#07101E" stroke="#2D4A6F" stroke-width="0.9"/>
  <text x="218" y="29" text-anchor="middle" fill="#34D399" font-family="system-ui,sans-serif" font-size="18.5" font-weight="900">+31.3%</text>
  <text x="218" y="42" text-anchor="middle" fill="#E2E8F0" font-family="system-ui,sans-serif" font-size="8" font-weight="800">$164.88 CLOSE</text>
  <text x="218" y="55" text-anchor="middle" fill="#93C5FD" font-family="system-ui,sans-serif" font-size="7.5" font-weight="800">S&amp;P +4.73%</text>
</svg>"""
    if kind == "refinery":
        return """<svg viewBox="0 0 264 88" width="100%" height="88" xmlns="http://www.w3.org/2000/svg">
  <rect width="264" height="88" fill="#182334"/>
  <rect y="64" width="264" height="24" fill="#253145"/>
  <!-- Lukoil Perm refinery towers & storage tanks -->
  <rect x="14" y="34" width="12" height="30" fill="#475569"/>
  <rect x="31" y="22" width="11" height="42" fill="#64748B"/>
  <rect x="48" y="40" width="26" height="24" fill="#334155"/>
  <rect x="80" y="28" width="12" height="36" fill="#475569"/>
  <rect x="98" y="44" width="28" height="20" fill="#334155"/>
  <rect x="132" y="48" width="32" height="16" rx="2" fill="#475569"/>
  <!-- Flames & smoke plumes -->
  <path d="M46,42 Q60,8 74,40 Q88,14 98,42 Z" fill="#EA580C"/>
  <path d="M53,42 Q62,18 71,41 Q80,24 89,42 Z" fill="#FACC15"/>
  <circle cx="66" cy="14" r="9" fill="#475569" opacity="0.6"/>
  <circle cx="84" cy="9" r="10" fill="#334155" opacity="0.5"/>
  <!-- Incoming drone -->
  <path d="M126,20 L146,25 L126,30 L130,25 Z" fill="#F8FAFC"/>
  <line x1="108" y1="25" x2="123" y2="25" stroke="#F87171" stroke-width="1.5" stroke-dasharray="3,2"/>
  <rect x="160" y="8" width="96" height="44" rx="3" fill="#0F172A" stroke="#EA580C" stroke-width="1"/>
  <text x="208" y="28" text-anchor="middle" fill="#FACC15" font-family="system-ui,sans-serif" font-size="18" font-weight="900">1,500 km</text>
  <text x="208" y="43" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="7.8" font-weight="800">PERM + ROSTOV</text>
  <text x="12" y="79" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="7.6" font-weight="800">KYIV ALSO CLAIMS BENGHAZI HIT</text>
</svg>"""
    return """<svg viewBox="0 0 264 88" width="100%" height="88" xmlns="http://www.w3.org/2000/svg">
  <rect width="264" height="88" fill="#D9E8F5"/>
  <rect y="64" width="264" height="24" fill="#334155"/>
  <line x1="12" y1="76" x2="252" y2="76" stroke="#CBD5E1" stroke-width="1.4" stroke-dasharray="8,7" opacity="0.6"/>
  <!-- Brussels Airport ATC Tower -->
  <rect x="20" y="28" width="14" height="36" fill="#475569"/>
  <polygon points="12,28 42,28 37,15 17,15" fill="#1E293B"/>
  <rect x="16" y="19" width="22" height="5" fill="#38BDF8"/>
  <line x1="27" y1="6" x2="27" y2="15" stroke="#1E293B" stroke-width="1.8"/>
  <circle cx="27" cy="6" r="2.2" fill="#DC2626"/>
  <!-- Grounded jet with red circle-slash -->
  <path d="M58,52 L110,52 L122,42 L128,42 L120,56 L58,56 Z" fill="#1E293B"/>
  <polygon points="76,52 90,39 96,39 87,52" fill="#475569"/>
  <circle cx="92" cy="48" r="20" fill="none" stroke="#DC2626" stroke-width="3.8"/>
  <line x1="78" y1="34" x2="106" y2="62" stroke="#DC2626" stroke-width="3.8"/>
  <rect x="150" y="8" width="106" height="44" rx="3" fill="#FFFFFF" stroke="#B91C1C" stroke-width="1.2"/>
  <text x="203" y="29" text-anchor="middle" fill="#B91C1C" font-family="system-ui,sans-serif" font-size="18.5" font-weight="900">06–20 UTC</text>
  <text x="203" y="43" text-anchor="middle" fill="#1E293B" font-family="system-ui,sans-serif" font-size="8" font-weight="900">ATC SHUTDOWN</text>
</svg>"""


def feature_art(kind: str) -> str:
    if kind == "spain":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#F2EAD8"/>
  <rect width="192" height="4" fill="#AA151B"/><rect y="4" width="192" height="3" fill="#F1BF00"/>
  <!-- Courthouse columns -->
  <polygon points="10,22 68,22 39,10" fill="#1E3A8A"/>
  <rect x="16" y="23" width="6" height="25" fill="#94A3B8"/>
  <rect x="36" y="23" width="6" height="25" fill="#94A3B8"/>
  <rect x="56" y="23" width="6" height="25" fill="#94A3B8"/>
  <rect x="8" y="48" width="62" height="4" fill="#1E3A8A"/>
  <!-- Scales & green amnesty stamp -->
  <rect x="78" y="14" width="104" height="26" rx="3" fill="#FFFFFF" stroke="#047857" stroke-width="1.8" transform="rotate(-4 130 27)"/>
  <text x="130" y="32" text-anchor="middle" fill="#047857" font-family="system-ui,sans-serif" font-size="14.5" font-weight="900" transform="rotate(-4 130 27)">AMNESTY</text>
</svg>"""
    if kind == "rohingya":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#E8F0F8"/>
  <rect y="40" width="192" height="18" fill="#14532D"/>
  <!-- UK Flag -->
  <g transform="translate(8,17)">
    <rect width="34" height="20" fill="#012169" rx="1"/>
    <path d="M0,0 L34,20 M34,0 L0,20" stroke="#FFFFFF" stroke-width="4"/>
    <path d="M0,0 L34,20 M34,0 L0,20" stroke="#C8102E" stroke-width="1.8"/>
    <path d="M17,0 V20 M0,10 H34" stroke="#FFFFFF" stroke-width="6"/>
    <path d="M17,0 V20 M0,10 H34" stroke="#C8102E" stroke-width="3.2"/>
  </g>
  <!-- Sanctions document -->
  <rect x="48" y="15" width="28" height="32" rx="2" fill="#FFFFFF" stroke="#475569" stroke-width="1"/>
  <line x1="53" y1="22" x2="71" y2="22" stroke="#94A3B8" stroke-width="1.4"/>
  <line x1="53" y1="27" x2="71" y2="27" stroke="#94A3B8" stroke-width="1.4"/>
  <circle cx="62" cy="38" r="5" fill="none" stroke="#B91C1C" stroke-width="1.8"/>
  <text x="134" y="24" text-anchor="middle" fill="#1E3A8A" font-family="system-ui,sans-serif" font-size="14" font-weight="900">5 GENERALS</text>
  <text x="134" y="36" text-anchor="middle" fill="#B91C1C" font-family="system-ui,sans-serif" font-size="7.4" font-weight="900">ROHINGYA GENOCIDE</text>
</svg>"""
    if kind == "nasa":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#0B1226"/>
  <circle cx="24" cy="14" r="1.4" fill="#F8FAFC"/><circle cx="78" cy="11" r="1.2" fill="#F8FAFC"/>
  <circle cx="152" cy="12" r="1.3" fill="#CBD5E1"/><circle cx="110" cy="18" r="1" fill="#94A3B8"/>
  <!-- Rising blue Earth -->
  <circle cx="28" cy="24" r="8" fill="#2563EB"/>
  <path d="M23,22 Q28,19 32,24 Q28,28 24,26 Z" fill="#4ADE80"/>
  <!-- Lunar crater ground -->
  <ellipse cx="96" cy="60" rx="108" ry="20" fill="#64748B"/>
  <ellipse cx="44" cy="50" rx="14" ry="4" fill="#475569"/>
  <!-- Glowing Lunar Reactor-1 -->
  <circle cx="88" cy="34" r="13" fill="#38BDF8" opacity="0.22"/>
  <rect x="81" y="24" width="14" height="20" rx="2" fill="#E2E8F0"/>
  <circle cx="88" cy="34" r="4.5" fill="#38BDF8"/>
  <line x1="72" y1="32" x2="81" y2="32" stroke="#94A3B8" stroke-width="2"/>
  <line x1="95" y1="32" x2="104" y2="32" stroke="#94A3B8" stroke-width="2"/>
  <rect x="116" y="10" width="68" height="28" rx="3" fill="#1E293B" stroke="#38BDF8" stroke-width="1"/>
  <text x="150" y="26" text-anchor="middle" fill="#38BDF8" font-family="system-ui,sans-serif" font-size="14" font-weight="900">20 kW</text>
  <text x="150" y="35" text-anchor="middle" fill="#E2E8F0" font-family="system-ui,sans-serif" font-size="6.8" font-weight="800">LR-1 · 2030</text>
</svg>"""
    if kind == "asia_mkt":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#111827"/>
  <g stroke="#1F2937" stroke-width="0.7">
    <line x1="0" y1="18" x2="192" y2="18"/><line x1="0" y1="38" x2="192" y2="38"/>
  </g>
  <polyline points="8,18 30,22 50,33 68,28 88,48 104,38" fill="none" stroke="#EF4444" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="88" cy="48" r="3.4" fill="#EF4444"/>
  <text x="146" y="21" text-anchor="middle" fill="#F87171" font-family="system-ui,sans-serif" font-size="16" font-weight="900">-5.8%</text>
  <rect x="110" y="26" width="74" height="13" rx="2" fill="#047857"/>
  <text x="147" y="35" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="7" font-weight="900">TAIWAN 150%</text>
</svg>"""
    if kind == "nhs":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#E6F4F1"/>
  <!-- Radiology scan monitor -->
  <rect x="8" y="8" width="70" height="42" rx="3" fill="#0F172A" stroke="#0F766E" stroke-width="1.4"/>
  <g stroke="#1E3A5F" stroke-width="0.6">
    <line x1="25" y1="8" x2="25" y2="50"/><line x1="43" y1="8" x2="43" y2="50"/><line x1="61" y1="8" x2="61" y2="50"/>
    <line x1="8" y1="22" x2="78" y2="22"/><line x1="8" y1="36" x2="78" y2="36"/>
  </g>
  <ellipse cx="42" cy="30" rx="18" ry="12" fill="#334155"/>
  <circle cx="50" cy="25" r="7.5" fill="none" stroke="#22D3EE" stroke-width="1.8" stroke-dasharray="2.5,1.5"/>
  <circle cx="50" cy="25" r="2" fill="#22D3EE"/>
  <rect x="12" y="11" width="20" height="9" rx="1" fill="#0284C7"/>
  <text x="22" y="17.8" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="6.4" font-weight="900">NHS</text>
  <text x="135" y="29" text-anchor="middle" fill="#0F766E" font-family="system-ui,sans-serif" font-size="18" font-weight="900">700,000</text>
  <text x="135" y="41" text-anchor="middle" fill="#1E293B" font-family="system-ui,sans-serif" font-size="7.4" font-weight="800">£10M AI TRIAL</text>
</svg>"""
    if kind == "fifa":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#14532D"/>
  <line x1="96" y1="0" x2="96" y2="58" stroke="#4ADE80" stroke-width="1.2" opacity="0.5"/>
  <circle cx="96" cy="29" r="13" fill="none" stroke="#4ADE80" stroke-width="1.2" opacity="0.5"/>
  <rect x="8" y="17" width="80" height="28" rx="3" fill="#0F172A" stroke="#FACC15" stroke-width="1.1"/>
  <text x="48" y="31" text-anchor="middle" fill="#FACC15" font-family="system-ui,sans-serif" font-size="13.5" font-weight="900">2031</text>
  <text x="48" y="41" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="6.8" font-weight="800">US·MX·CR·JM</text>
  <rect x="104" y="17" width="80" height="24" rx="3" fill="#1E3A8A" stroke="#FACC15" stroke-width="1.1"/>
  <text x="144" y="30" text-anchor="middle" fill="#FACC15" font-family="system-ui,sans-serif" font-size="13" font-weight="900">2035</text>
  <text x="144" y="38.5" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="6.8" font-weight="800">UK HOSTS</text>
</svg>"""
    if kind == "colombia":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#292524"/>
  <!-- Civic building & car blast -->
  <rect x="10" y="22" width="52" height="30" fill="#57534E"/>
  <rect x="16" y="28" width="8" height="8" fill="#A8A29E"/>
  <rect x="30" y="28" width="8" height="8" fill="#A8A29E"/>
  <rect x="44" y="28" width="8" height="8" fill="#A8A29E"/>
  <polygon points="62,35 70,23 74,35 86,29 78,40 88,49 74,46 69,55 64,45 52,47" fill="#EA580C"/>
  <circle cx="72" cy="40" r="5" fill="#FDE047"/>
  <!-- Urban drone -->
  <path d="M92,20 L106,23 L92,26 L95,23 Z" fill="#F8FAFC"/>
  <rect x="114" y="16" width="70" height="25" rx="3" fill="#991B1B"/>
  <text x="149" y="29" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="13" font-weight="900">21+ HURT</text>
  <text x="149" y="38" text-anchor="middle" fill="#FECACA" font-family="system-ui,sans-serif" font-size="6.5" font-weight="800">+ CÚCUTA DRONE</text>
</svg>"""
    if kind == "senegal":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#FEF3C7"/>
  <rect y="36" width="192" height="22" fill="#0369A1"/>
  <path d="M0,37 Q24,31 48,37 T96,37 T144,37 T192,37" fill="none" stroke="#BAE6FD" stroke-width="1.8"/>
  <polygon points="10,16 68,36 42,36" fill="#FDE047" opacity="0.35"/>
  <g transform="translate(56,36) rotate(-14)">
    <path d="M-26,0 Q0,-11 26,0 L20,6 L-20,6 Z" fill="#92400E" stroke="#451A03" stroke-width="1.2"/>
  </g>
  <text x="144" y="23" text-anchor="middle" fill="#9A3412" font-family="system-ui,sans-serif" font-size="18" font-weight="900">~100</text>
  <text x="144" y="33" text-anchor="middle" fill="#7C2D12" font-family="system-ui,sans-serif" font-size="7.2" font-weight="800">ABOARD</text>
</svg>"""
    if kind == "gulf_claim":
        return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="96" height="58" fill="#3B1D1D"/>
  <rect x="96" width="96" height="58" fill="#172554"/>
  <line x1="96" y1="0" x2="96" y2="58" stroke="#F8FAFC" stroke-width="1.4" stroke-dasharray="3,2"/>
  <!-- Jet silhouette on left -->
  <path d="M16,32 L50,26 L70,30 L50,36 L42,44 L36,36 L16,35 Z" fill="#FCA5A5"/>
  <text x="48" y="52" text-anchor="middle" fill="#FDE68A" font-family="system-ui,sans-serif" font-size="7.2" font-weight="800">F-16 CLAIM</text>
  <text x="144" y="16" text-anchor="middle" fill="#93C5FD" font-family="system-ui,sans-serif" font-size="7.4" font-weight="900">US DENIAL</text>
  <text x="144" y="31" text-anchor="middle" fill="#FFFFFF" font-family="system-ui,sans-serif" font-size="13.5" font-weight="900">24+ HIT</text>
  <text x="144" y="40" text-anchor="middle" fill="#BFDBFE" font-family="system-ui,sans-serif" font-size="6.8" font-weight="800">TREASURY</text>
</svg>"""
    # cricket
    return """<svg viewBox="0 0 192 58" width="100%" height="58" xmlns="http://www.w3.org/2000/svg">
  <rect width="192" height="58" fill="#E6F4EA"/>
  <rect y="40" width="192" height="18" fill="#166534"/>
  <rect x="18" y="17" width="4" height="26" fill="#B45309"/>
  <rect x="26" y="17" width="4" height="26" fill="#B45309"/>
  <rect x="34" y="17" width="4" height="26" fill="#B45309"/>
  <rect x="17" y="15" width="22" height="3" fill="#D97706"/>
  <circle cx="52" cy="35" r="6" fill="#DC2626" stroke="#FFFFFF" stroke-width="1.2"/>
  <text x="130" y="27" text-anchor="middle" fill="#14532D" font-family="system-ui,sans-serif" font-size="19" font-weight="900">239-5</text>
  <text x="130" y="37" text-anchor="middle" fill="#166534" font-family="system-ui,sans-serif" font-size="7.2" font-weight="800">DAY 5 DRAW · 120 OV</text>
</svg>"""


def status_pill(status: str) -> str:
    fg, bg = STATUS_BADGE[status]
    return f'<span class="sp" style="color:{fg};background:{bg}">{esc(status)}</span>'


def build_html(data: dict) -> str:
    utc_items = "".join(
        f'<div class="utc-item"><span class="utc-t">{esc(u["time"])}</span><span class="utc-l">{esc(u["label"])}</span></div>'
        for u in data["utc_timeline"]
    )
    reg_bars = "".join(
        f'<div class="reg-seg" style="flex:{r["count"]};background:{r["color"]}">{esc(r["name"])} {r["count"]}</div>'
        for r in data["region_counts"]
    )
    num_items = "".join(
        f'<div class="dn-item"><div class="dn-v">{esc(n["val"])}</div><div class="dn-d">{esc(n["desc"])}</div></div>'
        for n in data["day_numbers"]
    )
    heroes_html = []
    for st in data["heroes"]:
        col = REGION_COLORS[st["region"]]
        heroes_html.append(
            f"""<article class="hero-card">
  <div class="art-wrap hero-art">
    {hero_art(st["art"])}
    <div class="loc-tag"><span class="nd" style="background:{col}">{st["id"]}</span>{esc(st["loc"])}</div>
    <div class="st-corner">{status_pill(st["status"])}</div>
  </div>
  <div class="kicker" style="color:{col}">{esc(st["kicker"])}</div>
  <h2 class="hero-h">{esc(st["headline"])}</h2>
  <p class="hero-d">{esc(st["summary"])}</p>
  <div class="src">{esc(st["source"])}</div>
</article>"""
        )

    def render_feat_row(items):
        out = []
        for st in items:
            col = REGION_COLORS[st["region"]]
            out.append(
                f"""<article class="feat-card">
  <div class="art-wrap feat-art">
    {feature_art(st["art"])}
    <div class="loc-tag sm"><span class="nd sm" style="background:{col}">{st["id"]}</span>{esc(st["loc"])}</div>
    <div class="st-corner">{status_pill(st["status"])}</div>
  </div>
  <div class="kicker sm" style="color:{col}">{esc(st["kicker"])}</div>
  <h3 class="feat-h">{esc(st["headline"])}</h3>
  <p class="feat-d">{esc(st["summary"])}</p>
  <div class="src sm">{esc(st["source"])}</div>
</article>"""
            )
        return "".join(out)

    feat_row1 = render_feat_row(data["features"][:5])
    feat_row2 = render_feat_row(data["features"][5:])

    # 25 briefs in 2 clean, spacious columns: 13 left + 12 right
    briefs = data["briefs"]
    cols = [briefs[:13], briefs[13:]]
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
  font-size: 46px; font-weight: 900; line-height: 0.96;
  letter-spacing: -0.7px; color: #111110;
}}
.masthead .sub {{
  font-family: Georgia, "Times New Roman", serif;
  font-style: italic; font-size: 10.8px; color: #3F3D36;
  margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.reg-bar {{
  display: flex; height: 13.5px; border-radius: 2px; overflow: hidden; gap: 1px;
}}
.reg-seg {{
  color: #FFF; font-size: 7.5px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  white-space: nowrap; letter-spacing: 0.2px;
}}
.utc-bar {{
  display: flex; align-items: stretch; gap: 6px;
  background: #141E30; color: #F8FAFC; border-radius: 2px;
  padding: 2.5px 6px 2.5px 0;
}}
.utc-tag {{
  background: #B91C1C; color: #FFF; font-size: 7.5px; font-weight: 900;
  padding: 2px 7px; display: flex; align-items: center; text-align: center;
  line-height: 1.05; letter-spacing: 0.3px; flex-shrink: 0;
}}
.utc-items {{
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; flex: 1;
}}
.utc-item {{
  display: flex; flex-direction: column; align-items: center; text-align: center;
  border-left: 1px solid #2A3B57; padding-left: 3px;
}}
.utc-item:first-child {{ border-left: none; padding-left: 0; }}
.utc-t {{ font-size: 8.4px; font-weight: 900; color: #FDE047; line-height: 1.05; }}
.utc-l {{ font-size: 6.9px; font-weight: 600; color: #E2E8F0; line-height: 1.08; }}
.hero-band {{
  display: grid; grid-template-columns: 1fr 1fr 1fr 176px; gap: 9px;
  border-bottom: 1.5px solid #161614; padding-bottom: 5px;
}}
.hero-card {{
  display: flex; flex-direction: column; gap: 2.5px;
}}
.art-wrap {{
  position: relative; width: 100%; border: 1px solid #CFC8B8;
  border-radius: 2px; overflow: hidden;
}}
.hero-art {{ height: 88px; }}
.feat-art {{ height: 58px; }}
.loc-tag {{
  position: absolute; top: 3px; left: 3px;
  background: rgba(255,255,255,0.93); color: #111110;
  font-size: 6.8px; font-weight: 900; letter-spacing: 0.2px;
  padding: 1px 4px 1px 2px; border-radius: 2px;
  display: inline-flex; align-items: center; gap: 3px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}}
.loc-tag.sm {{ font-size: 6.2px; padding: 0.5px 3.5px 0.5px 1.5px; }}
.nd {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 12.5px; height: 12.5px; border-radius: 50%;
  color: #FFF; font-size: 7.4px; font-weight: 900;
}}
.nd.sm {{ width: 11px; height: 11px; font-size: 6.6px; }}
.st-corner {{
  position: absolute; bottom: 3px; right: 3px;
}}
.sp {{
  display: inline-block; font-size: 6.1px; font-weight: 900;
  padding: 1px 4px; border-radius: 2px; letter-spacing: 0.25px;
}}
.kicker {{
  font-size: 7.4px; font-weight: 800; letter-spacing: 0.25px; margin-top: 1px;
}}
.kicker.sm {{ font-size: 6.7px; }}
.hero-h {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 13.6px; font-weight: 800; line-height: 1.12; color: #111110;
}}
.hero-d {{
  font-size: 8.3px; line-height: 1.22; color: #2D2C28;
}}
.src {{
  font-size: 6.9px; font-weight: 700; color: #646158; margin-top: auto;
}}
.src.sm {{ font-size: 6.4px; }}
.day-nums {{
  background: #111B2E; color: #F8FAFC; border-radius: 3px;
  padding: 6px 8px; display: flex; flex-direction: column; justify-content: space-between;
}}
.dn-h {{
  font-size: 8px; font-weight: 900; letter-spacing: 0.45px; color: #F8FAFC;
  border-bottom: 1px solid #2A3C5A; padding-bottom: 2.5px;
}}
.dn-item {{ display: flex; flex-direction: column; }}
.dn-v {{
  font-family: Georgia, serif; font-size: 14.5px; font-weight: 900;
  color: #FBBF24; line-height: 1.02;
}}
.dn-d {{
  font-size: 6.8px; color: #CBD5E1; line-height: 1.12; font-weight: 600;
}}
.feats {{
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px;
}}
.feat-card {{
  display: flex; flex-direction: column; gap: 2px;
  border-bottom: 1px solid #D5CEBE; padding-bottom: 3.5px;
}}
.feat-h {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 10.6px; font-weight: 800; line-height: 1.12; color: #111110;
}}
.feat-d {{
  font-size: 7.55px; line-height: 1.19; color: #31302B;
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
  font-size: 8.4px; font-weight: 900; letter-spacing: 0.4px;
  color: #A61C1C; text-transform: uppercase;
  display: flex; justify-content: space-between; align-items: baseline;
}}
.sec-h span {{ font-size: 7px; font-weight: 600; color: #57534A; text-transform: none; letter-spacing: 0; }}
.map-box {{
  width: 248px; height: 196px; border: 1px solid #C6BFAE; border-radius: 3px; overflow: hidden;
}}
.reg-leg {{
  display: flex; flex-wrap: wrap; gap: 3px 8px;
  font-size: 7.3px; font-weight: 700; color: #2D2C28;
}}
.leg-item {{ display: inline-flex; align-items: center; gap: 3px; }}
.leg-item i {{ width: 7.2px; height: 7.2px; border-radius: 50%; display: inline-block; }}
.key-box {{
  background: #F2EDE1; border: 1px solid #D5CEBE; border-radius: 2px;
  padding: 4px 6px; margin-top: auto;
  font-size: 6.9px; line-height: 1.38; color: #2D2C28;
}}
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
  font-size: 8px; line-height: 1.17; color: #1F1E1B;
}}
.b-num {{
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 13.5px; height: 13.5px; border-radius: 50%;
  color: #FFF; font-size: 6.8px; font-weight: 800; margin-top: 0.5px; flex-shrink: 0;
}}
.b-txt b {{ color: #111110; }}
.b-src {{ color: #6B665B; font-size: 6.9px; font-weight: 600; }}
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
  font-size: 6.95px; line-height: 1.21; color: #262320;
}}
.footer {{
  display: flex; justify-content: space-between; align-items: center;
  font-size: 6.9px; color: #57534A; font-weight: 600;
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
  <section class="reg-bar">{reg_bars}</section>
  <section class="utc-bar">
    <div class="utc-tag">UTC</div>
    <div class="utc-items">{utc_items}</div>
  </section>
  <section class="hero-band">
    {"".join(heroes_html)}
    <aside class="day-nums">
      <div class="dn-h">THE DAY IN NUMBERS</div>
      {num_items}
    </aside>
  </section>
  <section class="feats">{feat_row1}</section>
  <section class="feats">{feat_row2}</section>
  <section class="bottom-grid">
    <div class="map-panel">
      <div class="sec-h">WHERE IT HAPPENED <span>pins #1–13 · dots #14–38</span></div>
      <div class="map-box">{world_svg}</div>
      <div class="reg-leg">{reg_legend}</div>
      <div class="key-box">
        <div>{status_pill("OFFICIAL")} court, agency or result · {status_pill("CONFIRMED")} 2+ outlets</div>
        <div style="margin-top:2px">{status_pill("REPORTED")} single outlet · {status_pill("CLAIM")} one side's word</div>
      </div>
    </div>
    <div class="briefs-panel">
      <div class="sec-h">ALSO ON MONDAY 23 NOVEMBER <span>25 more stories</span></div>
      <div class="b-cols">{"".join(brief_cols_html)}</div>
    </div>
  </section>
  <section class="date-check">
    <div class="dc-tag">DATE<br>CHECK</div>
    <div class="dc-body">{esc(data["date_check_text"])}</div>
  </section>
  <footer class="footer">
    <span>Monday 23 November 2026 · World Edition · Claims attributed; sources named on each story</span>
    <span>Sources: Reuters, AP, BBC, Al Jazeera, Guardian, NASA, NHS, FIFA, IMF, WFP</span>
  </footer>
</div>
</body>
</html>
"""


def main() -> None:
    with open(STORIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    total = len(data["heroes"]) + len(data["features"]) + len(data["briefs"])
    if total != 38:
        raise ValueError(f"Expected 38 stories, got {total}")

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
