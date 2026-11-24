#!/usr/bin/env python3
"""Write the Monday 23 November 2026 world-news front-page image to /output/entry.png.

The asset is a 1024x1024 PNG summarizing 38 stories from Monday 23 November 2026
across 7 regions (Europe, Asia, Africa, Middle East, Americas, Oceania, Global),
with 13 illustrated cards, UTC timeline, Day in Numbers panel, world map, and 25 briefs.
"""

import os
import shutil


def main() -> None:
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "entry.png")
    dst = os.path.join(out_dir, "entry.png")
    shutil.copy2(src, dst)
    written = os.path.getsize(dst)
    if written <= 0 or written > 1048576:
        raise RuntimeError(f"Unexpected entry.png size: {written} bytes")
    print(f"Written {written} bytes to {dst}")


if __name__ == "__main__":
    main()
