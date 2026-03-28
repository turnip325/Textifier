#!/usr/bin/env python3
# ocr.py — OCR pipeline for Textifier.
# Discovers images in ~/Source (ordered by creation time), preprocesses them
# for better accuracy, runs Tesseract OCR, and writes combined output to
# ~/DocDestination/{filename}.txt.  Also handles source purge.

import os
import re
from pathlib import Path

from PIL import Image
import pytesseract

SOURCE_DIR = Path.home() / 'Source'
DEST_DIR   = Path.home() / 'DocDestination'

# All image types Tesseract/Pillow can handle
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.webp'}


def get_image_files() -> list[Path]:
    """Return image files from ~/Source sorted by creation time (oldest first).

    Using ctime so that a batch of scanned pages dropped in sequence are
    processed in the order they were captured, regardless of filename.
    """
    if not SOURCE_DIR.exists():
        return []
    files = [
        f for f in SOURCE_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    ]
    # st_ctime is creation time on Linux (actually metadata-change time, but
    # for freshly copied files it reliably reflects drop order)
    return sorted(files, key=lambda f: os.stat(f).st_ctime)


def preprocess(img: Image.Image) -> Image.Image:
    """Prepare image for Tesseract.

    Greyscale conversion and upscaling small images are the two changes with
    the highest impact on OCR accuracy for typical document scans.
    """
    img = img.convert('L')   # greyscale — removes colour noise
    w, h = img.size
    # Tesseract performs best at ~300 DPI; upscale if the image is very small
    if w < 1000:
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
    # Cap extremely large images to avoid memory spikes (long edge ≤ 4000px)
    w, h = img.size
    if max(w, h) > 4000:
        scale = 4000 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img


def sanitize_filename(raw: str) -> str:
    """Return a safe stem for the output file.

    Strips the directory component and extension, replaces anything that
    isn't a word character, hyphen, dot, or space with an underscore.
    Falls back to 'output' if nothing remains.
    """
    stem = Path(raw).stem          # drop any extension the user typed
    safe = re.sub(r'[^\w\-. ]', '_', stem).strip()
    return safe if safe else 'output'


def run_ocr(filename: str) -> dict:
    """OCR all images in ~/Source and write combined text to ~/DocDestination.

    Images are processed in creation-time order.  Each page gets a separator
    header so the reader can trace text back to its source file.

    Returns:
        {"ok": True,  "pages": N, "output": "/path/to/file.txt"}
        {"ok": False, "error": "human-readable message"}
    """
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    files = get_image_files()
    if not files:
        return {"ok": False, "error": "No images found in ~/Source"}

    safe   = sanitize_filename(filename)
    dest   = DEST_DIR / f"{safe}.txt"

    parts = []
    for i, img_path in enumerate(files, start=1):
        try:
            img  = Image.open(img_path)
            img  = preprocess(img)
            text = pytesseract.image_to_string(img, lang='eng')
            parts.append(
                f"--- Page {i}: {img_path.name} ---\n{text.strip()}"
            )
        except Exception as exc:
            # Don't abort the whole batch for one bad image — note it inline
            parts.append(
                f"--- Page {i}: {img_path.name} --- [ERROR: {exc}]"
            )

    dest.write_text('\n\n'.join(parts), encoding='utf-8')
    return {"ok": True, "pages": len(files), "output": str(dest)}


def purge_source() -> dict:
    """Delete all recognised image files from ~/Source.

    Only removes files with extensions in IMAGE_EXTS — never touches .txt,
    .pdf, or anything else the user might have placed there accidentally.

    Returns:
        {"ok": True, "deleted": N}
    """
    files = get_image_files()
    for f in files:
        f.unlink()
    return {"ok": True, "deleted": len(files)}


def image_count() -> int:
    """Return the number of images currently waiting in ~/Source."""
    return len(get_image_files())
