import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capture import latest  # noqa: E402

CAPTURE = HERE / "capture.py"


def run_capture(env, question="how much after tax", svg=None, plate=None, labels=None,
                shape="quantity", metaphor="piles of coins", why="one coin = $5K", lang=None):
    tmp = Path(tempfile.mkdtemp())
    qf = tmp / "q.txt"
    qf.write_text(question, encoding="utf-8")
    cmd = [sys.executable, str(CAPTURE), "--question-file", str(qf),
           "--shape", shape, "--metaphor", metaphor, "--why", why]
    if svg is not None:
        sf = tmp / "a.svg"
        sf.write_text(svg, encoding="utf-8")
        cmd += ["--svg-file", str(sf)]
    if plate is not None:
        pf = tmp / "p.png"
        pf.write_bytes(plate)
        lf = tmp / "l.html"
        lf.write_text(labels or "<div class='tag'>$97K</div>", encoding="utf-8")
        cmd += ["--plate", str(pf), "--labels", str(lf)]
    if lang:
        cmd += ["--lang", lang]
    full_env = dict(os.environ)
    full_env.update(env)
    out = subprocess.run(cmd, env=full_env, check=True, capture_output=True, text=True)
    return Path(out.stdout.strip())


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.env = {"PICTURE_MODE_HOME": str(self.home)}

    def test_svg_capture_writes_three_files(self):
        out = run_capture(self.env, question="how much after tax",
                          svg="<svg viewBox='0 0 680 200'></svg>",
                          shape="quantity", metaphor="piles of coins", why="one coin = $5K")
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["answer.svg", "meta.json", "question.txt"])
        meta = json.loads((out / "meta.json").read_text())
        self.assertEqual(meta["shape"], "quantity")
        self.assertEqual(meta["kind"], "svg")
        self.assertEqual(meta["lang"], "en")
        self.assertEqual(meta["metaphor"], "piles of coins")
        self.assertEqual(meta["why"], "one coin = $5K")
        self.assertEqual((out / "question.txt").read_text(), "how much after tax")
        self.assertTrue(out.parent == self.home / "last")

    def test_plate_capture_writes_plate_and_labels(self):
        out = run_capture(self.env, plate=b"\x89PNG\r\n", labels="<div class='tag'>$97K</div>",
                          shape="quantity", lang="ru")
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["labels.html", "meta.json", "plate.png", "question.txt"])
        meta = json.loads((out / "meta.json").read_text())
        self.assertEqual(meta["kind"], "plate")
        self.assertEqual(meta["lang"], "ru")

    def test_rejects_svg_with_script(self):
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            run_capture(self.env, svg="<svg><script>1</script></svg>")
        self.assertIn("script", cm.exception.stderr)
        self.assertFalse((self.home / "last").exists() and any((self.home / "last").iterdir()))

    def test_rejects_missing_question(self):
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            run_capture(self.env, question="   ", svg="<svg></svg>")
        self.assertEqual(cm.exception.returncode, 1)
        self.assertIn("question", cm.exception.stderr)

    def test_rejects_unknown_shape(self):
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            run_capture(self.env, svg="<svg></svg>", shape="vibes")
        self.assertEqual(cm.exception.returncode, 2)

    def test_latest_returns_most_recent_then_second(self):
        first = run_capture(self.env, question="first", svg="<svg></svg>")
        time.sleep(1.1)
        second = run_capture(self.env, question="second", svg="<svg></svg>")
        self.assertEqual(latest(self.home), second)
        self.assertEqual(latest(self.home, 2), first)

    def test_latest_raises_when_empty(self):
        with self.assertRaises(FileNotFoundError) as cm:
            latest(self.home)
        self.assertIn("nothing captured yet", str(cm.exception))


    def test_rejects_svg_with_event_handler(self):
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            run_capture(self.env, svg='<svg onload="alert(1)"></svg>')
        self.assertIn("unsafe", cm.exception.stderr)

    def test_rejects_svg_with_foreign_object_or_javascript_href(self):
        for bad in ('<svg><foreignObject><iframe src="x"></iframe></foreignObject></svg>',
                    '<svg><a href="javascript:alert(1)"><text>x</text></a></svg>',
                    '<svg><image href="https://evil.example/x.png"/></svg>'):
            with self.subTest(bad=bad), self.assertRaises(subprocess.CalledProcessError) as cm:
                run_capture(self.env, svg=bad)
            self.assertIn("unsafe", cm.exception.stderr)

    def test_rejects_labels_with_script(self):
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            run_capture(self.env, plate=b"png", labels='<img src=x onerror="alert(1)">')
        self.assertIn("unsafe", cm.exception.stderr)

    def test_rejects_theme_variables_and_widget_classes(self):
        for bad in ('<svg><rect fill="var(--p)"/></svg>', '<svg><g class="c-blue"><rect/></g></svg>'):
            with self.subTest(bad=bad), self.assertRaises(subprocess.CalledProcessError) as cm:
                run_capture(self.env, svg=bad)
            self.assertIn("literal colours", cm.exception.stderr)

    def test_fresh_folder_survives_a_race_on_the_same_second(self):
        import capture
        from unittest import mock
        first = capture.write_capture(self.home, "q", "quantity", "m", "w", "en", svg="<svg></svg>")
        with mock.patch.object(capture.Path, "exists", return_value=False), \
             mock.patch.object(capture, "datetime", wraps=capture.datetime) as dt:
            dt.now.return_value = capture.datetime.strptime(first.name[:15], "%Y%m%d-%H%M%S")
            second = capture.write_capture(self.home, "q", "quantity", "m", "w", "en", svg="<svg></svg>")
        self.assertNotEqual(first, second)
        self.assertEqual(second.name, first.name + "-2")


from keep import slug  # noqa: E402

KEEP = HERE / "keep.py"


def git(repo, args):
    return subprocess.run(["git", "-C", str(repo)] + args.split(), check=True,
                          capture_output=True, text=True).stdout


def run_keep(env, n=None, scaled=False, check=True):
    cmd = [sys.executable, str(KEEP)]
    if n is not None:
        cmd.append(str(n))
    if scaled:
        cmd.append("--scaled")
    full_env = dict(os.environ)
    full_env.update(env)
    return subprocess.run(cmd, env=full_env, check=check, capture_output=True, text=True)



class EntryRef:
    """An entry folder read from a branch with git show, so tests never need the checkout."""
    def __init__(self, repo, branch, name):
        self.repo, self.branch, self.name = repo, branch, name
    def read(self, file):
        return subprocess.run(["git", "-C", str(self.repo), "show", f"{self.branch}:entries/{self.name}/{file}"],
                              check=True, capture_output=True, text=True).stdout
    def has(self, file):
        return subprocess.run(["git", "-C", str(self.repo), "cat-file", "-e", f"{self.branch}:entries/{self.name}/{file}"],
                              capture_output=True).returncode == 0


class KeepTests(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.env = {"PICTURE_MODE_HOME": str(self.home)}
        self.gallery = Path(tempfile.mkdtemp()) / "gallery"
        self.gallery.mkdir()
        git(self.gallery, "init -q -b main")
        git(self.gallery, "config user.email test@example.com")
        git(self.gallery, "config user.name test")
        (self.gallery / "README.md").write_text("# gallery\n")
        git(self.gallery, "add README.md")
        git(self.gallery, "commit -q -m init")
        (self.home / "config.json").write_text(json.dumps({"gallery": str(self.gallery)}))
        self.capture = run_capture(self.env, question="so how much will I get after tax from $80K",
                                   svg="<svg viewBox='0 0 680 200'></svg>")

    def branches(self):
        return [b.strip() for b in git(self.gallery, "branch --format=%(refname:short)").splitlines() if b.startswith("keep/")]

    def entries(self, branch=None):
        branch = branch or sorted(self.branches())[-1]
        names = git(self.gallery, f"ls-tree -d --name-only {branch}:entries").split()
        return [EntryRef(self.gallery, branch, n) for n in sorted(names)]

    def test_slug_basic(self):
        self.assertEqual(slug("so how much will I get after tax from $80K"), "so-how-much-will-i-get")

    def test_slug_cyrillic_is_empty_so_stamp_is_used(self):
        self.assertEqual(slug("ничего не понял"), "")

    def test_keep_copies_entry_and_commits_on_branch(self):
        out = run_keep(self.env)
        folders = self.entries()
        self.assertEqual(len(folders), 1)
        self.assertTrue(folders[0].name.endswith("-so-how-much-will-i-get"))
        self.assertTrue(folders[0].has("answer.svg"))
        self.assertEqual(folders[0].read("question.txt"), "so how much will I get after tax from $80K")
        meta = json.loads(folders[0].read("meta.json"))
        self.assertFalse(meta["scaled"])
        self.assertIn("kept", meta)
        self.assertEqual(self.branches(), ["keep/" + folders[0].name[11:]])
        self.assertIn("keep:", git(self.gallery, f"log -1 --format=%s {self.branches()[0]}"))
        self.assertIn(folders[0].name, out.stdout)
        self.assertIn("so how much will I get", out.stdout)

    def test_keep_leaves_the_checkout_alone(self):
        (self.gallery / "notes.txt").write_text("unrelated")
        git(self.gallery, "add notes.txt")
        run_keep(self.env)
        self.assertEqual(git(self.gallery, "rev-parse --abbrev-ref HEAD").strip(), "main")
        self.assertIn("A  notes.txt", git(self.gallery, "status --porcelain"))
        self.assertFalse((self.gallery / "entries").exists())
        branch = self.branches()[0]
        self.assertNotIn("notes.txt", git(self.gallery, f"show --name-only --format= {branch}"))
        self.assertEqual(len(git(self.gallery, "worktree list").splitlines()), 1)

    def test_each_keep_branches_from_main_not_from_the_previous_keep(self):
        run_keep(self.env)
        time.sleep(1.1)
        run_capture(self.env, question="a different question", svg="<svg></svg>")
        run_keep(self.env)
        main = git(self.gallery, "rev-parse main").strip()
        for b in self.branches():
            self.assertEqual(git(self.gallery, f"rev-parse {b}~1").strip(), main, b)

    def test_keep_folder_option_keeps_that_exact_capture(self):
        time.sleep(1.1)
        run_capture(self.env, question="another session's question", svg="<svg></svg>")
        cmd = [sys.executable, str(KEEP), "--folder", str(self.capture)]
        full_env = dict(os.environ); full_env.update(self.env)
        subprocess.run(cmd, env=full_env, check=True, capture_output=True, text=True)
        self.assertEqual(self.entries()[0].read("question.txt"), "so how much will I get after tax from $80K")

    def test_keep_second_capture_with_n2(self):
        time.sleep(1.1)
        run_capture(self.env, question="newer question here", svg="<svg></svg>")
        run_keep(self.env, n=2)
        folders = self.entries()
        self.assertEqual(len(folders), 1)
        self.assertEqual(folders[0].read("question.txt"), "so how much will I get after tax from $80K")

    def test_keep_same_question_twice_suffixes(self):
        git(self.gallery, "checkout -q -b seeded")
        (self.gallery / "entries" / "2026-01-01-x").mkdir(parents=True)
        run_keep(self.env)
        first = self.branches()[0]
        git(self.gallery, f"checkout -q main")
        git(self.gallery, f"merge -q --ff-only {first}")
        git(self.gallery, f"branch -q -D {first}")
        run_keep(self.env)
        names = [f.name for f in self.entries()]
        self.assertEqual(len(names), 2)
        self.assertTrue(names[1].endswith("-2"), names)

    def test_keep_cyrillic_question_uses_stamp(self):
        time.sleep(1.1)
        cap = run_capture(self.env, question="ничего не понял", svg="<svg></svg>", lang="ru")
        run_keep(self.env)
        names = [f.name for f in self.entries()]
        self.assertEqual(names, [f"{cap.name[:4]}-{cap.name[4:6]}-{cap.name[6:8]}-{cap.name}"])

    def test_keep_without_captures_exits_1(self):
        empty_home = Path(tempfile.mkdtemp())
        (empty_home / "config.json").write_text(json.dumps({"gallery": str(self.gallery)}))
        r = run_keep({"PICTURE_MODE_HOME": str(empty_home)}, check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("nothing captured yet", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_keep_without_config_exits_1(self):
        (self.home / "config.json").unlink()
        r = run_keep(self.env, check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("config.json", r.stderr)

    def test_scaled_flag(self):
        run_keep(self.env, scaled=True)
        meta = json.loads(self.entries()[0].read("meta.json"))
        self.assertTrue(meta["scaled"])

    def test_dry_run_changes_nothing(self):
        cmd = [sys.executable, str(KEEP), "--dry-run"]
        full_env = dict(os.environ); full_env.update(self.env)
        r = subprocess.run(cmd, env=full_env, check=True, capture_output=True, text=True)
        self.assertEqual(self.branches(), [])
        self.assertIn("would copy", r.stdout)


if __name__ == "__main__":
    unittest.main()
