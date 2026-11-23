#!/usr/bin/env python3
"""Copy pre-built editorial front-page image to /output/entry.png.

The image is a 1024x1024 PNG summarizing world news of 23 November 2026:
40 stories across 6 continents with 4 lead illustrated cards.
Build: python3 scripts/generate2.py regenerates assets/entry.png.
"""
import os, shutil

os.makedirs('/output', exist_ok=True)
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'entry.png')
dst = '/output/entry.png'
shutil.copy2(src, dst)
print(f'Written {os.path.getsize(dst)} bytes to /output/entry.png')