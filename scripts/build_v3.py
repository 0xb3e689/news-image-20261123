#!/usr/bin/env python3
"""Build final newspaper HTML from SVGs + template, screenshot with Chrome."""
import os, subprocess, shutil

HERE = os.path.dirname(os.path.abspath(__file__)) or '.'
ASSETS = os.path.join(HERE, '..', 'assets')

with open(os.path.join(ASSETS, 'template.html')) as f:
    html = f.read()

cards = [
    ('cop31.svg', 'EUROPE · CLIMATE', 'COP31 Collapses as EU Rejects Fossil Fuel Omission', '#B91C1C'),
    ('hormuz.svg', 'MIDDLE EAST · CONFLICT', 'Tankers Ablaze in Strait of Hormuz as IRGC Warns of Unrest', '#B45309'),
    ('markets.svg', 'ASIA · MARKETS', 'Asian Stocks Tumble on AI Bubble Fears; Anthropic Drops Toward $83', '#1D4ED8'),
    ('security.svg', 'AMERICAS · SECURITY', 'US Army Defies Court to Detonate Unstable Explosives in Iowa', '#7C3AED'),
    ('disaster.svg', 'ASIA · DISASTER', 'Indonesia Factory Fire Kills 3; Police Remove 24 Body Bags', '#047857'),
]

for i, (svg_file, kicker, headline, color) in enumerate(cards):
    with open(os.path.join(ASSETS, 'svg', svg_file)) as f:
        svg_content = f.read()
    art = f'<div class="art-box">{svg_content}</div>'
    cap = f'<div class="caption-box"><div class="kicker" style="color:{color}">{kicker}</div><div class="headline">{headline}</div></div>'
    html = html.replace(f'[CARD{i+1}_HTML]', art + cap)

out_html = os.path.join(ASSETS, 'page.html')
with open(out_html, 'w') as f:
    f.write(html)
print(f'HTML: {len(html)} bytes')

chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-sandbox',
    '--window-size=1024,1024', '--force-device-scale-factor=1', '--hide-scrollbars',
    '--screenshot=/tmp/news_entry.png', f'file://{out_html}'],
    capture_output=True, timeout=15)

out_png = os.path.join(ASSETS, 'entry.png')
if os.path.exists('/tmp/news_entry.png'):
    shutil.copy2('/tmp/news_entry.png', out_png)
    print(f'PNG: {os.path.getsize(out_png)} bytes')
else:
    print('FAIL: no screenshot')
    exit(1)
