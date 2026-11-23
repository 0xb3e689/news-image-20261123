#!/usr/bin/env python3
"""Copy pre-built entry.png to /output/entry.png."""
import os, shutil

os.makedirs('/output', exist_ok=True)
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'entry.png')
shutil.copy2(src, '/output/entry.png')
print(f'Copied {os.path.getsize(src)} bytes to /output/entry.png')