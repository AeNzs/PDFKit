"""Convert assets/applogo.png into a crisp multi-resolution Windows assets/applogo.ico."""

import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "applogo.png")
DST = os.path.join(ROOT, "assets", "applogo.ico")


def main() -> None:
    if not os.path.isfile(SRC):
        raise FileNotFoundError(f"Logo not found: {SRC}")
    img = Image.open(SRC).convert("RGBA")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(DST, format="ICO", sizes=sizes)
    print(f"Generated {DST} ({os.path.getsize(DST)} bytes)")


if __name__ == "__main__":
    main()
