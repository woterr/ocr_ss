#!/usr/bin/env python3

import subprocess
import datetime
import os
import sys

from ocr import extract_text

SAVE_DIR = os.path.expanduser("~/Pictures/Screenshots")
os.makedirs(SAVE_DIR, exist_ok=True)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
image_path = os.path.join(SAVE_DIR, f"screenshot_{timestamp}.png")
# text_path = os.path.join(SAVE_DIR, f"screenshot_{timestamp}.txt")

def run(cmd):
    return subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

try:
    geometry = run(["slurp"]).stdout.strip()
    if not geometry:
        sys.exit(0)

    run(["grim", "-g", geometry, image_path])

    with open(image_path, "rb") as f:
        subprocess.run(
            ["wl-copy", "--type", "image/png"],
            stdin=f,
            check=True
        )

    # OCR
    text = extract_text(image_path)
    print(text)

    # with open(text_path, "w", encoding="utf-8") as f:
    #     f.write(text)

    # subprocess.run(
    #     ["wl-copy"],
    #     input=text,
    #     text=True,
    #     check=True
    # )

    subprocess.run([
        "notify-send",
        "Screenshot",
        "Image and text copied"
    ])

except subprocess.CalledProcessError as e:
    subprocess.run([
        "notify-send",
        "Screenshot failed",
        e.stderr or "Unknown error"
    ])
