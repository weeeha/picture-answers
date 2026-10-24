#!/usr/bin/env python3
"""Copy the Nth-last picture-mode capture into the gallery repo on a keep/ branch.

Usage: keep.py [N | --folder PATH] [--scaled] [--dry-run]
Reads $PICTURE_MODE_HOME/config.json: {"gallery": "/abs/path/to/repo"}.
Works in a temporary git worktree branched from main, so the gallery checkout is never touched.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import home_dir, latest  # noqa: E402


def slug(question: str) -> str:
    words = re.findall(r"[a-z0-9]+", question.lower())[:6]
    return "-".join(words)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def _entry_folder(tree: Path, capture: Path, question: str) -> Path:
    stamp = capture.name
    day = f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"
    base = tree / "entries" / f"{day}-{slug(question) or stamp}"
    folder, k = base, 1
    while folder.exists():
        k += 1
        folder = base.with_name(f"{base.name}-{k}")
    return folder


def _branch_exists(repo: Path, name: str) -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", "-q", f"refs/heads/{name}"], cwd=repo,
                          capture_output=True).returncode == 0


def _branch_name(repo: Path, folder_name: str) -> str:
    candidates = ["keep/" + folder_name[11:], "keep/" + folder_name]
    for c in candidates:
        if not _branch_exists(repo, c):
            return c
    k = 2
    while _branch_exists(repo, f"{candidates[1]}-{k}"):
        k += 1
    return f"{candidates[1]}-{k}"


def _base_ref(repo: Path) -> str:
    for ref in ("origin/main", "main"):
        if subprocess.run(["git", "rev-parse", "--verify", "-q", ref], cwd=repo, capture_output=True).returncode == 0:
            return ref
    raise FileNotFoundError(f"gallery has no main branch: {repo}")


def keep(home: Path, n: int = 1, scaled: bool = False, dry_run: bool = False,
         folder: Path | None = None) -> tuple[str, str, str]:
    """Returns (entry path inside the gallery, branch, question)."""
    config = Path(home) / "config.json"
    if not config.exists():
        raise FileNotFoundError(f"no gallery configured: write {config} with {{\"gallery\": \"/path\"}}")
    try:
        gallery = Path(json.loads(config.read_text())["gallery"]).expanduser()
    except (KeyError, ValueError):
        raise FileNotFoundError(f"{config} needs a \"gallery\" path")
    if not (gallery / ".git").exists():
        raise FileNotFoundError(f"gallery is not a git repo: {gallery}")
    capture = Path(folder) if folder else latest(home, n)
    if not (capture / "question.txt").exists():
        raise FileNotFoundError(f"not a capture folder: {capture}")
    question = (capture / "question.txt").read_text(encoding="utf-8")
    base = _base_ref(gallery)
    tree = Path(tempfile.mkdtemp(prefix="picture-keep-")) / "tree"
    _git(gallery, "worktree", "add", "-q", "--detach", str(tree), base)
    try:
        target = _entry_folder(tree, capture, question)
        branch = _branch_name(gallery, target.name)
        rel = str(target.relative_to(tree))
        if dry_run:
            return rel, branch, question
        shutil.copytree(capture, target)
        meta_path = target / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["scaled"] = bool(scaled)
        meta["kept"] = date.today().isoformat()
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _git(tree, "checkout", "-q", "-b", branch)
        _git(tree, "add", rel)
        title = " ".join(question.split())[:60]
        _git(tree, "commit", "-q", "-m", f"keep: {title}", "--", rel)
        return rel, branch, question
    finally:
        _git(gallery, "worktree", "remove", "--force", str(tree))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("n", nargs="?", type=int, default=1, help="1 = most recent capture")
    ap.add_argument("--folder", help="the exact capture folder capture.py printed; wins over N")
    ap.add_argument("--scaled", action="store_true", help="numbers were scaled to illustrative values")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.n < 1:
            raise ValueError("N starts at 1, the most recent capture")
        rel, branch, question = keep(home_dir(), a.n, a.scaled, a.dry_run, Path(a.folder) if a.folder else None)
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print(f"git failed: {e.stderr or e}", file=sys.stderr)
        return 1
    first = " ".join(question.split())[:80]
    if a.dry_run:
        print(f"would copy \"{first}\" into {rel} on branch {branch}")
    else:
        print(f"kept \"{first}\"\n{rel}\nbranch {branch} (from main; push it and open a PR)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
