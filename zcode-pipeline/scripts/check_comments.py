#!/usr/bin/env python3
"""Mechanical comment counter for delivery diffs (zcode-pipeline payload).

Fail = any comment line (added or surviving in a touched hunk), any comment
syntax family, any language. Detection contract: architecture §4.2 of epic
no-comments-hardening — the sole source of truth. stdout-only; exits
0 = clean, 1 = hits found, 2 = environment/usage problem.
"""
import argparse
import os
import re
import subprocess
import sys
from fnmatch import fnmatch

SLASH_FAMILY = ["js", "jsx", "mjs", "cjs", "ts", "tsx", "java", "kt", "kts",
                "swift", "go", "rs", "cs", "c", "h", "cpp", "cc", "cxx",
                "hpp", "hh", "scala", "dart", "zig", "php", "groovy", "gradle"]
HASH_FAMILY = ["py", "pyw", "sh", "bash", "zsh", "rb", "pl", "pm", "r", "R",
               "yaml", "yml", "toml", "ini", "cfg", "conf", "env", "tf", "jl"]
PYTHON_SUFFIXES = ["py", "pyw"]
DASH_FAMILY = ["sql", "lua"]
BLOCK_ONLY_FAMILY = ["css", "scss", "less"]
MARKUP_FAMILY = ["md", "markdown", "html", "htm", "xml", "svg", "vue"]
FIXTURE_DIR_PARTS = ["__snapshots__/", "testdata/", "test-data/", "fixtures/"]
FIXTURE_SUFFIXES = [".snap"]

LINE_MARKERS: dict[str, list[str]] = {
    "python": ["#"],
    "hash": ["#"],
    "slash": ["//"],
    "dash": ["--"],
    "block": [],
    "markup": [],
    "vue": ["//"],
    "generic": ["//"],
    "json": [],
}
BLOCK_PAIRS: dict[str, list[tuple[str, str]]] = {
    "python": [("/*", "*/")],
    "hash": [("/*", "*/")],
    "slash": [("/*", "*/")],
    "dash": [],
    "block": [("/*", "*/")],
    "markup": [("<!--", "-->")],
    "vue": [("<!--", "-->"), ("/*", "*/")],
    "generic": [("<!--", "-->"), ("/*", "*/")],
    "json": [],
}
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
LICENSE_HEADER_ZONE = 20
LICENSE_LINE = re.compile(
    r"SPDX-License-Identifier|Copyright\s*[(\xa9@]|All rights reserved"
    r"|Mozilla Public License|Apache License|GNU (General Public|Affero|Lesser)"
    r" Public License|\bMIT License\b|\bBSD [0-9]\b|This Source Code Form is subject"
    r"|Licensed under|LICENSE for terms|Use of this source code is governed"
    r"|permission notice|obtain one at")
BINARY_LINE = re.compile(r"^Binary files .* and (.+) differ$")
SURVIVING_NOTE = "note: surviving detection limited to -U3 context of touched hunks"
FAIL_VERDICT = ("FAIL: {count} comment line(s) in the delivery diff — remove them "
                "or obtain an explicit user-sanctioned exception")


def git_lines(repo: str, args: list[str]) -> list[str]:
    proc = subprocess.run(["git", "-c", "core.quotePath=false"] + args, cwd=repo,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or f"git exited with code {proc.returncode}")
    return proc.stdout.decode("utf-8", errors="replace").splitlines()


def resolve_base(repo: str, explicit: str | None) -> str | None:
    if explicit:
        if explicit.startswith("-"):
            raise RuntimeError(f"invalid base ref: {explicit}")
        return explicit
    for branch in ["main", "master"]:
        try:
            lines = git_lines(repo, ["merge-base", branch, "HEAD"])
        except RuntimeError:
            continue
        if lines:
            return lines[0].strip()
    return None


def file_suffix(path: str) -> str:
    name = os.path.basename(path.replace(os.sep, "/"))
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[1]


def syntax_family(suffix: str) -> str:
    if suffix == "json":
        return "json"
    if suffix in PYTHON_SUFFIXES:
        return "python"
    if suffix in SLASH_FAMILY:
        return "slash"
    if suffix in HASH_FAMILY:
        return "hash"
    if suffix in DASH_FAMILY:
        return "dash"
    if suffix in BLOCK_ONLY_FAMILY:
        return "block"
    if suffix in MARKUP_FAMILY:
        return "vue" if suffix == "vue" else "markup"
    return "generic"


def is_fixture_path(path: str) -> bool:
    norm = path.replace(os.sep, "/")
    dir_parts = [part + "/" for part in norm.split("/")[:-1]]
    if any(part in FIXTURE_DIR_PARTS for part in dir_parts):
        return True
    return any(norm.endswith(suffix) for suffix in FIXTURE_SUFFIXES)


def path_selected(path: str, selectors: list[str]) -> bool:
    if not selectors:
        return True
    norm = path.replace(os.sep, "/")
    for selector in selectors:
        cand = selector.replace(os.sep, "/").rstrip("/")
        if norm == cand or norm.startswith(cand + "/") or fnmatch(norm, cand):
            return True
    return False


def has_cyrillic(line: str) -> bool:
    return any(0x0400 <= ord(ch) <= 0x04FF for ch in line)


def display_text(line: str) -> str:
    text = line.rstrip("\r")
    if len(text) > 120:
        return text[:120] + "..."
    return text


def strip_string_literals(line: str) -> str:
    out: list[str] = []
    delim = ""
    i = 0
    while i < len(line):
        ch = line[i]
        if delim:
            if ch == "\\":
                out.append("  ")
                i += 2
                continue
            if ch == delim:
                delim = ""
            out.append(" ")
            i += 1
            continue
        if ch in "'\"`":
            delim = ch
            out.append(" ")
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def classify_line(stripped: str, markers: list[str]) -> bool:
    for marker in markers:
        pos = stripped.find(marker)
        while pos != -1:
            if pos == 0 or stripped[pos - 1].isspace():
                return True
            pos = stripped.find(marker, pos + 1)
    return False


def block_comment_lines(lines: list[str], opener: str, closer: str) -> set[int]:
    hits: set[int] = set()
    inside = False
    for idx, line in enumerate(lines):
        intersects = inside
        pos = 0
        while pos < len(line):
            if inside:
                end = line.find(closer, pos)
                if end == -1:
                    pos = len(line)
                else:
                    inside = False
                    pos = end + len(closer)
            else:
                start = line.find(opener, pos)
                if start == -1:
                    pos = len(line)
                else:
                    inside = True
                    intersects = True
                    pos = start + len(opener)
        if intersects:
            hits.add(idx)
    return hits


def python_triple_processing(lines: list[str]) -> tuple[set[int], list[str]]:
    doc_lines: set[int] = set()
    masked: list[str] = []
    delim = ""
    in_doc = False
    for idx, raw in enumerate(lines):
        out: list[str] = []
        i = 0
        if delim and in_doc and not raw:
            doc_lines.add(idx)
        while i < len(raw):
            if delim:
                end = raw.find(delim, i)
                if end == -1:
                    out.append(" " * (len(raw) - i))
                    if in_doc:
                        doc_lines.add(idx)
                    i = len(raw)
                else:
                    out.append(" " * (end + 3 - i))
                    if in_doc:
                        doc_lines.add(idx)
                    i = end + 3
                    delim = ""
            else:
                dq = raw.find('"""', i)
                sq = raw.find("'''", i)
                if dq == -1 and sq == -1:
                    out.append(raw[i:])
                    break
                if dq == -1 or (sq != -1 and sq < dq):
                    start, delim = sq, "'''"
                else:
                    start, delim = dq, '"""'
                out.append(raw[i:start])
                statement_leading = raw[:start].strip() == ""
                in_doc = statement_leading
                end = raw.find(delim, start + 3)
                if end == -1:
                    out.append(" " * (len(raw) - start))
                    i = len(raw)
                    if in_doc:
                        doc_lines.add(idx)
                else:
                    out.append(" " * (end + 3 - start))
                    i = end + 3
                    delim = ""
                    if in_doc:
                        doc_lines.add(idx)
        masked.append("".join(out))
    return doc_lines, masked


def scan_file(lines: list[str], family: str) -> list[int]:
    if family == "json":
        return []
    work = list(lines)
    doc_lines: set[int] = set()
    if family == "python":
        doc_lines, work = python_triple_processing(work)
    stripped = [strip_string_literals(line) for line in work]
    hits = set(doc_lines)
    for opener, closer in BLOCK_PAIRS[family]:
        hits |= block_comment_lines(stripped, opener, closer)
    markers = LINE_MARKERS[family]
    for idx, line in enumerate(stripped):
        if idx == 0 and line.strip().startswith("#!"):
            hits.discard(idx)
            continue
        if classify_line(line, markers):
            hits.add(idx)
    return sorted(hit + 1 for hit in hits)


def parse_diff(diff_lines: list[str]) -> tuple[
        dict[str, dict[int, tuple[str, str]]], dict[str, int], list[str]]:
    files: dict[str, dict[int, tuple[str, str]]] = {}
    hunk_counts: dict[str, int] = {}
    binary: list[str] = []
    current: dict[int, tuple[str, str]] | None = None
    current_path: str | None = None
    section_hunks = 0
    in_hunk = False
    line_no = 0
    for line in diff_lines:
        if line.startswith("diff --git "):
            if current_path is not None:
                hunk_counts[current_path] = section_hunks
            current = None
            current_path = None
            section_hunks = 0
            in_hunk = False
            continue
        binary_match = BINARY_LINE.match(line)
        if binary_match:
            target = binary_match.group(1)
            if target.startswith("b/"):
                target = target[2:]
            if target != "/dev/null" and target not in binary:
                binary.append(target)
            current = None
            continue
        if not in_hunk and line.startswith("+++ "):
            target = line[4:].strip()
            if target.startswith('"') and target.endswith('"'):
                target = target[1:-1]
            if target == "/dev/null":
                current = None
            else:
                if target.startswith("b/"):
                    target = target[2:]
                current = files.setdefault(target, {})
                current_path = target
            continue
        match = HUNK_HEADER.match(line)
        if match:
            in_hunk = True
            section_hunks += 1
            line_no = int(match.group(1))
            continue
        if not in_hunk or current is None or line.startswith("\\"):
            continue
        if line.startswith("+"):
            current[line_no] = ("added", line[1:])
            line_no += 1
        elif line.startswith("-"):
            continue
        else:
            current[line_no] = ("surviving", line[1:])
            line_no += 1
    if current_path is not None:
        hunk_counts[current_path] = section_hunks
    return files, hunk_counts, binary


def collect_untracked(repo: str, selectors: list[str]) -> list[str]:
    found: list[str] = []
    for line in git_lines(repo, ["status", "--porcelain"]):
        if not line.startswith("?? "):
            continue
        entry = line[3:].strip()
        if entry.startswith('"') and entry.endswith('"'):
            entry = entry[1:-1]
        if entry.endswith("/"):
            listed = git_lines(repo, ["ls-files", "--others", "--exclude-standard", "--", entry])
            found.extend(listed)
        else:
            found.append(entry)
    unique = list(dict.fromkeys(found))
    return [path for path in unique if path_selected(path, selectors)]


def load_text(abs_path: str) -> tuple[str, bool] | None:
    try:
        with open(abs_path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\x00" in raw:
        return ("", True)
    return (raw.decode("utf-8", errors="replace"), False)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="check_comments.py",
        usage="python3 check_comments.py [--base REF] [--paths PATH [PATH ...]]",
    )
    parser.add_argument("--base", default=None, help="base ref of the delivery diff")
    parser.add_argument("--paths", nargs="+", default=[], metavar="PATH",
                        help="limit the check to these repo-relative paths")
    args = parser.parse_args()
    try:
        repo = git_lines(".", ["rev-parse", "--show-toplevel"])[0].strip()
        base = resolve_base(repo, args.base)
        if base is None:
            print("error: cannot resolve the base ref (main/master); pass --base REF explicitly",
                  file=sys.stderr)
            sys.exit(2)
        diff_args = ["diff", "-U3", base]
        if args.paths:
            diff_args += ["--"] + args.paths
        diff_lines = git_lines(repo, diff_args)
        untracked = collect_untracked(repo, args.paths)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"error: git not available ({exc})", file=sys.stderr)
        sys.exit(2)
    files, hunk_counts, binary_paths = parse_diff(diff_lines)
    notes = [f"skipped binary file: {path}" for path in binary_paths]
    generic_files: list[str] = []
    hits: list[tuple[str, int, str, str, bool, str]] = []
    reviewed = 0
    scanned_hunks = 0
    plans = [(path, lines, False) for path, lines in files.items()]
    plans += [(path, None, True) for path in untracked]
    for path, hunk_lines, is_untracked in plans:
        if is_fixture_path(path):
            notes.append(f"skipped fixture path: {path}")
            continue
        loaded = load_text(os.path.join(repo, path))
        if loaded is None:
            notes.append(f"skipped unreadable file: {path}")
            continue
        text, is_binary = loaded
        if is_binary:
            notes.append(f"skipped binary file: {path}")
            continue
        lines = text.split("\n")
        family = syntax_family(file_suffix(path))
        if family == "generic":
            generic_files.append(path)
        comment_numbers = scan_file(lines, family)
        exempt_numbers = set()
        zone = sorted(n for n in comment_numbers if n <= LICENSE_HEADER_ZONE)
        run: list[int] = []
        for n in zone:
            if run and n == run[-1] + 1:
                run.append(n)
                continue
            if run and any(LICENSE_LINE.search(lines[m - 1]) for m in run):
                exempt_numbers.update(run)
            run = [n]
        if run and any(LICENSE_LINE.search(lines[m - 1]) for m in run):
            exempt_numbers.update(run)
        reviewed += 1
        scanned_hunks += hunk_counts.get(path, 0)
        if is_untracked:
            scanned_hunks += 1
        for number in comment_numbers:
            if number > len(lines):
                continue
            recorded = hunk_lines.get(number) if hunk_lines is not None else None
            if recorded is None and not is_untracked:
                continue
            if number in exempt_numbers:
                notes.append(f"exempt license header line: {path}:{number}")
                continue
            raw_line = lines[number - 1]
            kind = recorded[0] if recorded is not None else "added"
            hits.append((path, number, kind, family,
                         has_cyrillic(raw_line), display_text(raw_line)))
    for note in dict.fromkeys(notes):
        print(note)
    for path in generic_files:
        print(f"generic-syntax file: {path}")
    if not hits:
        print(f"OK: {reviewed} file(s), {scanned_hunks} hunks, 0 comment lines.")
        print(SURVIVING_NOTE)
        sys.exit(0)
    hits.sort(key=lambda hit: (hit[0], hit[1]))
    for path, number, kind, family, cyr, text in hits:
        flag = " [cyr]" if cyr else ""
        print(f"{path}:{number} {kind} {family}{flag} {text}")
    print(FAIL_VERDICT.format(count=len(hits)))
    print(SURVIVING_NOTE)
    sys.exit(1)


if __name__ == "__main__":
    main()
