#!/usr/bin/env python3

import subprocess
import datetime
import os
import sys

from ocr import extract_text
from viewer import Viewer

SAVE_DIR = os.path.expanduser("~/Pictures/Screenshots")
os.makedirs(SAVE_DIR, exist_ok=True)

def run(cmd):
    return subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
image_path = os.path.join(SAVE_DIR, f"screenshot_{timestamp}.png")

try:
    geometry = run(["slurp"]).stdout.strip()
    if not geometry:
        sys.exit(0)

    run(["grim", "-g", geometry, image_path])

    # copy image
    with open(image_path, "rb") as f:
        subprocess.run(
            ["wl-copy", "--type", "image/png"],
            stdin=f,
            check=True
        )

    boxes = extract_text(image_path)

    app = Viewer(image_path, boxes)
    app.run()

except subprocess.CalledProcessError as e:
    subprocess.run([
        "notify-send",
        "Screenshot failed",
        e.stderr or "Unknown error"
    ])
