#!/usr/bin/env python3
"""Save a picture-mode answer and its question to disk before it is shown.

Writes $PICTURE_MODE_HOME/last/<YYYYMMDD-HHMMSS>/ with question.txt, meta.json and
either answer.svg or (plate.png + labels.html). Prints the folder path.
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

SHAPES = ("quantity", "mechanism", "comparison", "status")

# Markup that can run code or pull from elsewhere once the gallery inlines a capture.
UNSAFE = re.compile(
    r"<\s*(script|foreignobject|iframe|object|embed)\b"
    r"|\son[a-z]+\s*="
    r"|javascript:"
    r"|(?:xlink:)?href\s*=\s*[\"']?\s*(?:https?:|//|data:)",
    re.IGNORECASE,
)
# Theme hooks that only exist inside the chat widget; the gallery would paint them black.
THEMED = re.compile(r"var\(--|class=\"[^\"]*\bc-[a-z]+", re.IGNORECASE)


def check_markup(markup: str, what: str) -> None:
    hit = UNSAFE.search(markup)
    if hit:
        raise ValueError(f"unsafe markup in {what}: {hit.group(0).strip()!r}; capture static markup only")
    if what == "svg" and THEMED.search(markup):
        raise ValueError("svg uses widget theme variables or c-* classes; draw with literal colours on a paper background")


def home_dir() -> Path:
    return Path(os.environ.get("PICTURE_MODE_HOME", str(Path.home() / ".claude" / "picture-mode")))


def latest(home: Path, n: int = 1) -> Path:
    """The Nth most recent capture folder under home/last (1 = newest)."""
    last = Path(home) / "last"
    folders = sorted((p for p in last.iterdir() if p.is_dir()), key=lambda p: p.name) if last.is_dir() else []
    if len(folders) < n:
        raise FileNotFoundError("nothing captured yet" if not folders else f"only {len(folders)} captured")
    return folders[-n]


def _fresh_folder(home: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    last = Path(home) / "last"
    last.mkdir(parents=True, exist_ok=True)
    k = 1
    while True:
        folder = last / (stamp if k == 1 else f"{stamp}-{k}")
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            k += 1


def write_capture(home: Path, question: str, shape: str, metaphor: str, why: str, lang: str,
                  svg: str | None = None, plate: Path | None = None, labels: str | None = None) -> Path:
    if not question or not question.strip():
        raise ValueError("question is empty")
    if shape not in SHAPES:
        raise ValueError(f"shape must be one of {', '.join(SHAPES)}")
    if svg is not None:
        check_markup(svg, "svg")
        kind = "svg"
    elif plate is not None and labels is not None:
        check_markup(labels, "labels")
        kind = "plate"
    else:
        raise ValueError("give --svg-file, or --plate together with --labels")
    folder = _fresh_folder(home)
    (folder / "question.txt").write_text(question, encoding="utf-8")
    if kind == "svg":
        (folder / "answer.svg").write_text(svg, encoding="utf-8")
    else:
        shutil.copyfile(plate, folder / "plate.png")
        (folder / "labels.html").write_text(labels, encoding="utf-8")
    meta = {
        "stamp": folder.name,
        "date": datetime.now().date().isoformat(),
        "shape": shape,
        "metaphor": metaphor,
        "why": why,
        "lang": lang,
        "kind": kind,
    }
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return folder


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--question-file", required=True)
    ap.add_argument("--svg-file")
    ap.add_argument("--plate")
    ap.add_argument("--labels")
    ap.add_argument("--shape", required=True)
    ap.add_argument("--metaphor", required=True)
    ap.add_argument("--why", required=True)
    ap.add_argument("--lang", default="en")
    a = ap.parse_args(argv)
    if a.shape not in SHAPES:
        print(f"shape must be one of {', '.join(SHAPES)}", file=sys.stderr)
        return 2
    try:
        question = Path(a.question_file).read_text(encoding="utf-8")
        svg = Path(a.svg_file).read_text(encoding="utf-8") if a.svg_file else None
        labels = Path(a.labels).read_text(encoding="utf-8") if a.labels else None
        plate = Path(a.plate) if a.plate else None
        folder = write_capture(home_dir(), question, a.shape, a.metaphor, a.why, a.lang, svg, plate, labels)
    except (ValueError, OSError) as e:
        print(str(e), file=sys.stderr)
        return 1
    print(folder)
    return 0


if __name__ == "__main__":
    sys.exit(main())
