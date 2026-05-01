"""Stdlib-only test that helper-index.json is well-formed and consistent with _helpers.py."""
import ast
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "reference" / "helper-index.json"
HELPERS_PATH = REPO_ROOT / "scripts" / "_helpers.py"

REQUIRED_KEYS = (
    "name",
    "signature",
    "category",
    "return",
    "side_effects",
    "idempotency",
    "notes",
)
ALLOWED_IDEMPOTENCY = {"yes", "no", "partial", "unknown"}
ALLOWED_CATEGORIES = {
    "scene",
    "mesh",
    "materials",
    "lighting",
    "camera",
    "render",
    "animation",
    "import_export",
    "geometry_nodes",
    "utility",
    "other",
}


class TestRun:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def check(self, name, ok, detail=""):
        tag = "PASS" if ok else "FAIL"
        line = "[%s] %s" % (tag, name)
        if detail:
            line += " -- " + detail
        print(line)
        if ok:
            self.passed += 1
        else:
            self.failed += 1


def load_index():
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def parse_helpers():
    src = HELPERS_PATH.read_text(encoding="utf-8")
    return ast.parse(src, filename=str(HELPERS_PATH))


def top_level_func_names(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names


def main():
    t = TestRun()

    # 1. valid JSON
    try:
        index = load_index()
        t.check("helper-index.json is valid JSON", True, "%d entries" % len(index))
    except FileNotFoundError:
        t.check("helper-index.json is valid JSON", False, "file not found")
        print("Summary: %d passed, %d failed" % (t.passed, t.failed))
        sys.exit(1)
    except json.JSONDecodeError as e:
        t.check("helper-index.json is valid JSON", False, str(e))
        print("Summary: %d passed, %d failed" % (t.passed, t.failed))
        sys.exit(1)

    if not isinstance(index, list):
        t.check("helper-index.json is a list", False, "type=%s" % type(index).__name__)
        print("Summary: %d passed, %d failed" % (t.passed, t.failed))
        sys.exit(1)
    t.check("helper-index.json is a list", True)

    # 2. required keys
    missing_total = 0
    for i, entry in enumerate(index):
        if not isinstance(entry, dict):
            t.check("entry %d is dict" % i, False, "type=%s" % type(entry).__name__)
            missing_total += 1
            continue
        missing = [k for k in REQUIRED_KEYS if k not in entry]
        if missing:
            t.check(
                "entry %d (%s) has all required keys"
                % (i, entry.get("name", "?")),
                False,
                "missing: " + ", ".join(missing),
            )
            missing_total += 1
    if missing_total == 0:
        t.check("all entries have required keys", True, "%d entries" % len(index))

    # 3. unique names
    names = [e.get("name") for e in index if isinstance(e, dict)]
    dupes = sorted({n for n in names if names.count(n) > 1})
    t.check(
        "all entry names are unique",
        not dupes,
        "duplicates: " + ", ".join(dupes) if dupes else "%d unique" % len(set(names)),
    )

    # 4. signature starts with name + "("
    sig_bad = []
    for e in index:
        if not isinstance(e, dict):
            continue
        n = e.get("name", "")
        s = e.get("signature", "")
        if not isinstance(s, str) or not s.startswith(n + "("):
            sig_bad.append(n)
    t.check(
        "signature starts with name + '('",
        not sig_bad,
        ("offenders: " + ", ".join(sig_bad)) if sig_bad else "%d ok" % len(index),
    )

    # 5. idempotency in allowed set
    idem_bad = []
    for e in index:
        if not isinstance(e, dict):
            continue
        v = e.get("idempotency")
        if v not in ALLOWED_IDEMPOTENCY:
            idem_bad.append("%s=%r" % (e.get("name", "?"), v))
    t.check(
        "idempotency in {yes,no,partial,unknown}",
        not idem_bad,
        ("offenders: " + "; ".join(idem_bad)) if idem_bad else "all valid",
    )

    # 6. category in allowed set
    cat_bad = []
    for e in index:
        if not isinstance(e, dict):
            continue
        v = e.get("category")
        if v not in ALLOWED_CATEGORIES:
            cat_bad.append("%s=%r" % (e.get("name", "?"), v))
    t.check(
        "category in agreed set",
        not cat_bad,
        ("offenders: " + "; ".join(cat_bad)) if cat_bad else "all valid",
    )

    # 7. every name has matching def in _helpers.py
    try:
        tree = parse_helpers()
        helper_names = top_level_func_names(tree)
        missing_defs = sorted(n for n in names if n and n not in helper_names)
        t.check(
            "every index name has top-level def in _helpers.py",
            not missing_defs,
            ("missing: " + ", ".join(missing_defs))
            if missing_defs
            else "%d resolved" % len(names),
        )
    except FileNotFoundError:
        t.check(
            "every index name has top-level def in _helpers.py",
            False,
            "scripts/_helpers.py not found",
        )
    except SyntaxError as e:
        t.check(
            "every index name has top-level def in _helpers.py",
            False,
            "_helpers.py SyntaxError: %s" % e,
        )

    print("-" * 60)
    print("Summary: %d passed, %d failed" % (t.passed, t.failed))
    sys.exit(0 if t.failed == 0 else 1)


if __name__ == "__main__":
    main()
