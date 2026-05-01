"""Stdlib-only validator for the blender skill repo. Exits non-zero on any failure."""
import ast
import json
import os
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


class Result:
    __slots__ = ("ok", "msg")

    def __init__(self, ok, msg):
        self.ok = ok
        self.msg = msg

    def __repr__(self):
        tag = "[OK]  " if self.ok else "[FAIL]"
        return tag + " " + self.msg


def parse_frontmatter(text):
    """Tiny YAML-ish parser for `key: value` lines between --- markers.

    Returns (dict, error_message_or_none)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "SKILL.md does not start with '---' frontmatter marker"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "SKILL.md frontmatter has no closing '---' marker"
    data = {}
    for raw in lines[1:end]:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            return None, "Frontmatter line missing ':' -> %r" % raw
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if (value.startswith("\"") and value.endswith("\"")) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        data[key] = value
    return data, None


def check_skill_md_and_frontmatter(results):
    skill_path = REPO_ROOT / "SKILL.md"
    if not skill_path.exists():
        results.append(Result(False, "SKILL.md missing at %s" % skill_path))
        return None
    text = skill_path.read_text(encoding="utf-8")
    fm, err = parse_frontmatter(text)
    if err is not None:
        results.append(Result(False, "SKILL.md frontmatter: %s" % err))
        return None
    results.append(Result(True, "SKILL.md exists and has frontmatter"))

    ok = True
    if "name" not in fm:
        results.append(Result(False, "frontmatter missing 'name'"))
        ok = False
    else:
        if not NAME_RE.match(fm["name"]):
            results.append(
                Result(False, "frontmatter 'name' invalid: %r" % fm["name"])
            )
            ok = False
        else:
            results.append(Result(True, "frontmatter name=%s" % fm["name"]))

    if "description" not in fm or not fm["description"]:
        results.append(Result(False, "frontmatter missing/empty 'description'"))
        ok = False
    else:
        if len(fm["description"]) > 300:
            results.append(
                Result(
                    False,
                    "frontmatter 'description' too long (%d chars > 300)"
                    % len(fm["description"]),
                )
            )
            ok = False
        else:
            results.append(
                Result(
                    True,
                    "frontmatter description present (%d chars)"
                    % len(fm["description"]),
                )
            )

    if "version" in fm:
        if not VERSION_RE.match(fm["version"]):
            results.append(
                Result(False, "frontmatter 'version' invalid: %r" % fm["version"])
            )
            ok = False
        else:
            results.append(Result(True, "frontmatter version=%s" % fm["version"]))

    return fm if ok else None


def check_all_json_files(results):
    """Validate every *.json file in the repo (excluding .git/__pycache__)."""
    bad = 0
    total = 0
    for jp in REPO_ROOT.rglob("*.json"):
        rel = jp.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(".git/") or "__pycache__" in rel:
            continue
        total += 1
        try:
            json.loads(jp.read_text(encoding="utf-8"))
        except Exception as e:
            results.append(Result(False, "JSON invalid: %s -- %s" % (rel, e)))
            bad += 1
    if bad == 0 and total > 0:
        results.append(Result(True, "all %d JSON files parse cleanly" % total))
    elif total == 0:
        results.append(Result(True, "no JSON files found (skipped)"))


def collect_md_files():
    files = []
    for top in ("SKILL.md", "README.md"):
        p = REPO_ROOT / top
        if p.exists():
            files.append(p)
    for sub in ("reference", "docs"):
        d = REPO_ROOT / sub
        if d.is_dir():
            for p in d.rglob("*.md"):
                files.append(p)
    return files


def check_markdown_links(results):
    md_files = collect_md_files()
    broken = []
    checked = 0
    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8")
        except Exception as e:
            results.append(Result(False, "cannot read %s: %s" % (md, e)))
            continue
        for m in LINK_RE.finditer(text):
            target = m.group(2).strip()
            # Strip trailing whitespace inside link parens like "(path "title")"
            target = target.split()[0] if target else target
            if not target:
                continue
            if target.startswith("#"):
                continue
            low = target.lower()
            if low.startswith("http://") or low.startswith("https://"):
                continue
            if low.startswith("mailto:"):
                continue
            # Strip anchor / query
            path_part = target.split("#", 1)[0].split("?", 1)[0]
            if not path_part:
                continue
            resolved = (md.parent / path_part).resolve()
            checked += 1
            if not resolved.exists():
                broken.append((md, target, resolved))
    if broken:
        for md, target, resolved in broken:
            results.append(
                Result(
                    False,
                    "broken link in %s -> %s (resolved=%s)"
                    % (md.relative_to(REPO_ROOT), target, resolved),
                )
            )
    else:
        results.append(
            Result(
                True,
                "markdown links: %d resolved across %d files"
                % (checked, len(md_files)),
            )
        )
    return len(broken)


def check_helpers_parse(results):
    p = REPO_ROOT / "scripts" / "_helpers.py"
    if not p.exists():
        results.append(Result(False, "scripts/_helpers.py missing"))
        return None
    src = p.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(p))
    except SyntaxError as e:
        results.append(
            Result(
                False,
                "scripts/_helpers.py SyntaxError line %s col %s: %s"
                % (e.lineno, e.offset, e.msg),
            )
        )
        return None
    results.append(Result(True, "scripts/_helpers.py parses cleanly"))
    return tree


REQUIRED_INDEX_KEYS = (
    "name",
    "signature",
    "category",
    "return",
    "side_effects",
    "idempotency",
    "notes",
)


def check_helper_index_json(results):
    p = REPO_ROOT / "reference" / "helper-index.json"
    if not p.exists():
        results.append(Result(False, "reference/helper-index.json missing"))
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        results.append(Result(False, "helper-index.json invalid JSON: %s" % e))
        return None
    if not isinstance(data, list):
        results.append(Result(False, "helper-index.json must be a JSON list"))
        return None
    bad = 0
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            results.append(Result(False, "helper-index.json entry %d not a dict" % i))
            bad += 1
            continue
        missing = [k for k in REQUIRED_INDEX_KEYS if k not in entry]
        if missing:
            results.append(
                Result(
                    False,
                    "helper-index.json entry %d (%s) missing keys: %s"
                    % (i, entry.get("name", "?"), ", ".join(missing)),
                )
            )
            bad += 1
    if bad == 0:
        results.append(
            Result(True, "helper-index.json valid (%d entries)" % len(data))
        )
    return data


def load_allowlist():
    p = REPO_ROOT / "reference" / "helper-index.allowlist"
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.add(s)
    return out


def public_top_level_funcs(tree):
    names = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.append(node.name)
    return names


def check_index_consistency(results, tree, index):
    if tree is None or index is None:
        results.append(
            Result(False, "skipping index<->helpers consistency (prior failure)")
        )
        return
    helper_names = set(public_top_level_funcs(tree))
    allow = load_allowlist()
    index_names = []
    for e in index:
        if isinstance(e, dict) and "name" in e:
            index_names.append(e["name"])
    index_set = set(index_names)

    missing_in_helpers = sorted(n for n in index_set if n not in helper_names)
    missing_in_index = sorted(
        n for n in helper_names if n not in index_set and n not in allow
    )

    if missing_in_helpers:
        results.append(
            Result(
                False,
                "index lists names with no matching helper: %s"
                % ", ".join(missing_in_helpers),
            )
        )
    else:
        results.append(
            Result(
                True,
                "all %d index names map to public helpers" % len(index_set),
            )
        )
    if missing_in_index:
        results.append(
            Result(
                False,
                "public helpers missing from index (and not allowlisted): %s"
                % ", ".join(missing_in_index),
            )
        )
    else:
        results.append(
            Result(
                True,
                "all %d public helpers are indexed or allowlisted"
                % len(helper_names),
            )
        )


def main():
    results = []
    print("Validating skill at %s" % REPO_ROOT)
    print("-" * 60)

    check_skill_md_and_frontmatter(results)
    broken = check_markdown_links(results)
    tree = check_helpers_parse(results)
    index = check_helper_index_json(results)
    check_index_consistency(results, tree, index)
    check_all_json_files(results)

    for r in results:
        print(r)

    failed = [r for r in results if not r.ok]
    print("-" * 60)
    if failed:
        print("FAILED: %d of %d checks failed" % (len(failed), len(results)))
        sys.exit(1)
    else:
        public_count = 0
        if tree is not None:
            public_count = len(public_top_level_funcs(tree))
        print(
            "Skill validation OK: %d public helpers indexed, %d broken links, frontmatter valid"
            % (public_count, broken or 0)
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
