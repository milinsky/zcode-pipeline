#!/usr/bin/env python3
"""Deterministic post-epic artifact cleanup core for the zcode-pipeline plugin
(zcode-pipeline payload, sibling of check_comments.py).

Scan/plan mode (default) prints one JSON plan document to stdout and mutates
nothing. Apply mode (--apply FILE|-) re-validates every target against the
red lines, realpath containment, tracked-any and running-container gates at
apply time - the plan is never a permission to bypass the gates - and removes
exactly the confirmed targets. Git is strictly read-only. Exits 0 = plan
built / apply completed, 1 = apply partially failed, 2 = environment/usage.
Refusals are plan data (the "refused" section), not script errors.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from fnmatch import fnmatchcase

STACK_SIGNATURES: dict[str, list[str]] = {
    "rust": ["Cargo.toml"],
    "node": ["package.json"],
    "python": ["pyproject.toml", "requirements.txt"],
    "php": ["composer.json"],
    "go": ["go.mod"],
    "ruby": ["Gemfile"],
    "jvm": ["pom.xml", "build.gradle*"],
    "elixir": ["mix.exs"],
    "deno": ["deno.json"],
    "tauri": ["tauri.conf.json", "src-tauri/tauri.conf.json"],
    "docker": ["Dockerfile", "docker-compose*.yml"],
}

STACK_DERIVATIONS: dict[str, list[str]] = {
    "rust": ["target/"],
    "node": ["node_modules/"],
    "python": [".venv/", "venv/", "__pycache__/"],
    "tauri": ["src-tauri/target/"],
}

REBUILD_HINTS: dict[str, str] = {
    "target/": "full cargo rebuild, typically 10-20 min",
    "node_modules/": "package manager reinstall",
    "src-tauri/target/": "full cargo rebuild, typically 10-20 min",
}

SHAPE_TOKENS: list[str] = [
    "target", "build", "dist", "out", "bin", "obj", "node_modules",
    "__pycache__", ".cache", ".tmp", ".tmpdir", "cache", "tmp", "temp",
    ".pytest_cache", ".mypy_cache", ".gradle", ".terraform",
    "cmake-build-*", "*-build", "build-*",
]

RED_LINE_PREFIXES: list[str] = [".ai/", ".git/"]

CLEAR_EVIDENCE: frozenset[str] = frozenset(
    ["stack-derived", "manifest", "profile", "docker-label"])
AMBIGUOUS_EVIDENCE: frozenset[str] = frozenset(["shape-sign", "docker-naming", "agent"])
EVIDENCE_RANK: dict[str, int] = {
    "stack-derived": 0, "manifest": 1, "profile": 1, "docker-label": 2,
    "shape-sign": 3, "docker-naming": 4, "agent": 4,
}
REFUSAL_ORDER: list[str] = [
    "red-line", "outside-project", "symlink-escape", "tracked-files", "running-container",
]
MANIFEST_KINDS: frozenset[str] = frozenset(["dir", "image", "container", "file"])
DOCKER_LABEL_KEY: str = "zcode-pipeline.project="
INSPECT_LABEL_KEY: str = "zcode-pipeline.project"
RUNNING_STATUSES: frozenset[str] = frozenset(["running", "paused", "restarting", "removing"])
PS_FORMAT: str = "{{.ID}}\\t{{.Names}}\\t{{.Status}}"
IMAGE_FORMAT: str = "{{.ID}}\\t{{.Repository}}\\t{{.Tag}}\\t{{.Size}}"
REBUILD_RUNNING: str = "recreatable from the project sources if still needed"
REBUILD_GENERIC: str = "regenerable"
NOTE_DOCKER_ABSENT: str = "docker CLI absent - docker attribution skipped"
USAGE_EXIT: int = 2


class UsageError(Exception):
    pass


@dataclass
class Candidate:
    kind: str
    ref: str
    key: str
    evidence: str
    size_bytes: int = 0
    pattern: str = ""
    docker_status: str = ""


@dataclass
class ProfileData:
    path: str | None
    clean_dirs: list[str] = field(default_factory=list)
    clean_globs: list[tuple[str, re.Pattern[str]]] = field(default_factory=list)
    keep_dirs: list[str] = field(default_factory=list)
    keep_globs: list[tuple[str, re.Pattern[str]]] = field(default_factory=list)
    docker_names: list[str] = field(default_factory=list)
    rebuild_globs: list[tuple[re.Pattern[str], str]] = field(default_factory=list)


def run_capture(argv: list[str], cwd: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def first_line(text: str) -> str:
    lines = text.strip().splitlines()
    message = lines[0] if lines else ""
    return message or "unknown error"


def git_repo_state(root: str) -> tuple[bool, str]:
    if shutil.which("git") is None:
        return False, "git binary not found"
    proc = run_capture(["git", "rev-parse", "--show-toplevel"], root)
    if proc.returncode != 0:
        return False, first_line(proc.stderr.decode("utf-8", errors="replace"))
    return True, ""


def git_lines(root: str, args: list[str]) -> list[str] | None:
    proc = run_capture(["git", "-c", "core.quotePath=false"] + args, root)
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", errors="replace").splitlines()


def commit_timestamp(root: str, rel: str) -> int | None:
    args = ["log", "-1", "--format=%ct"]
    if rel:
        args += ["--", rel]
    lines = git_lines(root, args)
    if not lines:
        return None
    try:
        return int(lines[0].strip())
    except ValueError:
        return None


def normalize_rel(raw: str) -> str:
    unified = raw.replace("\\", "/").strip().strip("/")
    while unified.startswith("./"):
        unified = unified[2:]
    if not unified:
        return ""
    resolved: list[str] = []
    for part in unified.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if resolved:
                resolved.pop()
            else:
                resolved.append(part)
        else:
            resolved.append(part)
    return "/".join(resolved)


def is_red_line(rel: str) -> bool:
    normalized = rel.strip("/")
    if not normalized:
        return False
    return any(
        normalized == prefix.rstrip("/") or normalized.startswith(prefix)
        for prefix in RED_LINE_PREFIXES
    )


def containment_reason(root_real: str, rel: str) -> str | None:
    current = root_real
    link_seen = False
    for part in rel.split("/"):
        current = os.path.join(current, part)
        if os.path.islink(current):
            link_seen = True
        resolved = os.path.realpath(current)
        if resolved != root_real and not resolved.startswith(root_real + os.sep):
            return "symlink-escape" if link_seen else "outside-project"
    return None


def fs_key(root_real: str, rel: str) -> str:
    return "fs:" + os.path.realpath(os.path.join(root_real, rel))


def compile_glob(pattern: str) -> re.Pattern[str]:
    out: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            out.append("(?:[^/]+/)*")
            index += 3
        elif pattern.startswith("**", index):
            out.append(".*")
            index += 2
        elif pattern[index] == "*":
            out.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(pattern[index]))
            index += 1
    return re.compile("".join(out))


def sanitize_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", name.lower())
    return slug or "project"


def status_is_running(status: str) -> bool:
    words = re.findall(r"[a-z]+", status.lower())
    if not words:
        return False
    if words[0] == "up":
        return True
    return any(word in RUNNING_STATUSES for word in words)


def docker_status_stopped(status: str) -> bool:
    return "exited" in status.lower()


def shape_name_matches(name: str) -> bool:
    return any(fnmatchcase(name, token) for token in SHAPE_TOKENS)


def is_kept(rel: str, profile: ProfileData) -> bool:
    if rel in profile.keep_dirs:
        return True
    return any(compiled.fullmatch(rel) is not None for _, compiled in profile.keep_globs)


def contains_kept(rel: str, kept_paths: list[str]) -> bool:
    return any(path.startswith(rel + "/") for path in kept_paths)


def detection_names(root: str) -> list[str]:
    names: list[str] = []
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return names
    for entry in entries:
        path = os.path.join(root, entry)
        if os.path.isfile(path):
            names.append(entry)
    for entry in entries:
        path = os.path.join(root, entry)
        if not os.path.isdir(path) or os.path.islink(path) or is_red_line(entry):
            continue
        try:
            sub_entries = sorted(os.listdir(path))
        except OSError:
            continue
        for name in sub_entries:
            if os.path.isfile(os.path.join(path, name)):
                names.append(f"{entry}/{name}")
    return names


def detect_stacks(root: str) -> list[str]:
    names = detection_names(root)
    found: list[str] = []
    for stack, signatures in STACK_SIGNATURES.items():
        if any(fnmatchcase(name, signature) for signature in signatures for name in names):
            found.append(stack)
    return found


def tracked_state(git_ok: bool, root: str, rel: str) -> str:
    if not git_ok:
        return "unknown"
    lines = git_lines(root, ["ls-files", "--", rel])
    if lines is None:
        return "unknown"
    return "tracked" if lines else "untracked"


def freshness_ok(root: str, rel: str, cand_mtime: float, git_ok: bool,
                 head_ts: int | None, notes: list[str]) -> bool:
    parent_rel = "/".join(rel.split("/")[:-1])
    if git_ok:
        timestamp = commit_timestamp(root, parent_rel)
        if timestamp is None:
            timestamp = head_ts
        if timestamp is not None:
            return cand_mtime > timestamp
        notes.append("no commit history: freshness uses mtime only")
    try:
        parent_path = os.path.join(root, parent_rel) if parent_rel else root
        parent_mtime = os.lstat(parent_path).st_mtime
    except OSError:
        return True
    return cand_mtime > parent_mtime


def tree_size(path: str, notes: list[str]) -> int:
    total = 0
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            entry = os.path.join(base, name)
            try:
                total += os.lstat(entry).st_size
            except OSError as exc:
                notes.append(f"size stat failed for {entry}: {exc.strerror}")
    return total


def size_of(target: str, notes: list[str]) -> int:
    try:
        if os.path.isdir(target) and not os.path.islink(target):
            return tree_size(target, notes)
        return os.lstat(target).st_size
    except OSError as exc:
        notes.append(f"size stat failed for {target}: {exc.strerror}")
        return 0


def walk_tree(root: str, profile: ProfileData, kept_paths: list[str],
              notes: list[str]) -> tuple[list[tuple[str, float]], list[str]]:
    dirs_out: list[tuple[str, float]] = []
    files_out: list[str] = []

    def on_error(err: OSError) -> None:
        notes.append(f"walk error: {err.strerror or 'unknown'} at {err.filename or 'unknown'}")

    for base, dirnames, filenames in os.walk(root, followlinks=False, onerror=on_error):
        dirnames.sort()
        filenames.sort()
        rel_base = os.path.relpath(base, root).replace(os.sep, "/")
        if rel_base == ".":
            rel_base = ""
        kept: list[str] = []
        for dirname in dirnames:
            rel_dir = f"{rel_base}/{dirname}" if rel_base else dirname
            if is_red_line(rel_dir):
                continue
            if is_kept(rel_dir, profile):
                if rel_dir not in kept_paths:
                    kept_paths.append(rel_dir)
                continue
            kept.append(dirname)
            try:
                mtime = os.lstat(os.path.join(base, dirname)).st_mtime
            except OSError as exc:
                notes.append(f"stat failed for {rel_dir}: {exc.strerror}")
                continue
            dirs_out.append((rel_dir, mtime))
        dirnames[:] = kept
        for filename in filenames:
            rel_file = f"{rel_base}/{filename}" if rel_base else filename
            if is_red_line(rel_file):
                continue
            if is_kept(rel_file, profile):
                if rel_file not in kept_paths:
                    kept_paths.append(rel_file)
                continue
            files_out.append(rel_file)
    dirs_out.sort()
    return dirs_out, files_out


def manifest_paths(root: str) -> list[str]:
    state_dir = os.path.join(root, ".ai", "state")
    try:
        entries = sorted(os.listdir(state_dir))
    except OSError:
        return []
    return [os.path.join(state_dir, entry) for entry in entries if entry.endswith("-artifacts.md")]


def parse_manifest_line(body: str) -> tuple[str, str] | None:
    kind = ""
    ref = ""
    for token in body[2:].split():
        if token.startswith("kind="):
            kind = token[5:]
        elif token.startswith("ref="):
            ref = token[4:]
    if kind in MANIFEST_KINDS and ref:
        return kind, ref
    return None


def manifest_layer(root: str, root_real: str, slug: str, notes: list[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    docker_present = shutil.which("docker") is not None
    for path in manifest_paths(root):
        try:
            with open(path, encoding="utf-8") as handle:
                lines = handle.read().splitlines()
        except OSError as exc:
            notes.append(f"manifest unreadable: {path} ({exc.strerror})")
            continue
        for line in lines:
            body = line.strip()
            if not body.startswith("- ") or "kind=" not in body:
                continue
            parsed = parse_manifest_line(body)
            if parsed is None:
                notes.append(f"manifest line skipped (malformed or unknown kind): {body[:120]}")
                continue
            kind, ref = parsed
            if kind in ("image", "container"):
                if not docker_present:
                    notes.append(f"manifest docker ref skipped (docker CLI absent): {ref}")
                    continue
                state, object_id, status, label_value = inspect_ref(root, ref, kind, slug)
                if state == "gone":
                    notes.append(f"manifest docker ref not found: {ref}")
                    continue
                if state == "error":
                    notes.append(f"docker unavailable: {status}")
                    continue
                if label_value and label_value != slug:
                    notes.append(
                        f"manifest docker ref skipped (labeled to another project): {ref}")
                    continue
                if (kind == "container" and not status_is_running(status)
                        and not docker_status_stopped(status)):
                    notes.append(f"manifest docker ref skipped (unknown status): {ref} ({status})")
                    continue
                candidates.append(Candidate(
                    kind=kind, ref=object_id, key=f"docker:{object_id}",
                    evidence="manifest" if label_value == slug else "docker-naming",
                    docker_status=status))
                continue
            rel = normalize_rel(ref)
            if not rel:
                notes.append(f"manifest ref resolves to the project root: {ref}")
                continue
            if is_red_line(rel):
                candidates.append(Candidate(
                    kind=kind, ref=rel, key=fs_key(root_real, rel), evidence="manifest"))
                continue
            target = os.path.join(root, rel)
            if not os.path.exists(target):
                notes.append(f"manifest ref not found: {rel}")
                continue
            actual_kind = "dir" if os.path.isdir(target) and not os.path.islink(target) else "file"
            candidates.append(Candidate(
                kind=actual_kind, ref=rel, key=fs_key(root_real, rel),
                evidence="manifest", size_bytes=size_of(target, notes)))
    return candidates


def parse_profile(root: str, notes: list[str]) -> ProfileData:
    path = os.path.join(root, ".ai", "cleanup-profile.md")
    profile = ProfileData(path=path if os.path.isfile(path) else None)
    if profile.path is None:
        return profile
    try:
        with open(profile.path, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        notes.append(f"profile unreadable: {exc.strerror}")
        profile.path = None
        return profile
    for line in lines:
        body = line.strip()
        if not body or body.startswith("#") or body.startswith("**"):
            continue
        key, sep, rest = body.partition("=")
        if not sep:
            continue
        if key in ("clean", "keep"):
            target_kind, sep2, value = rest.partition("=")
            if not sep2 or target_kind not in ("dir", "glob") or not value:
                notes.append(f"profile line skipped (malformed): {body[:120]}")
                continue
            if target_kind == "dir":
                target_list = profile.clean_dirs if key == "clean" else profile.keep_dirs
                target_list.append(normalize_rel(value))
            else:
                glob_list = profile.clean_globs if key == "clean" else profile.keep_globs
                glob_list.append((value, compile_glob(value)))
        elif key == "docker-name":
            if rest.strip():
                profile.docker_names.append(rest.strip())
            else:
                notes.append(f"profile line skipped (malformed): {body[:120]}")
        elif key == "rebuild":
            match = re.match(r"^(?:dir|glob)=(\S+) cost=(.+)$", rest)
            if match:
                profile.rebuild_globs.append((compile_glob(match.group(1)), match.group(2).strip()))
            else:
                notes.append(f"profile line skipped (malformed): {body[:120]}")
        else:
            notes.append(f"profile line skipped (unknown key): {key}")
    return profile


def profile_layer(root: str, root_real: str, walk_dirs: list[tuple[str, float]],
                  walk_files: list[str], profile: ProfileData,
                  notes: list[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    if profile.path is None:
        return candidates
    for raw_rel in profile.clean_dirs:
        rel = normalize_rel(raw_rel)
        if not rel:
            notes.append(f"profile clean target resolves to the project root: {raw_rel}")
            continue
        if is_red_line(rel):
            candidates.append(Candidate(
                kind="dir", ref=rel, key=fs_key(root_real, rel), evidence="profile"))
            continue
        target = os.path.join(root, rel)
        if not os.path.exists(target):
            notes.append(f"profile clean target not found: {rel}")
            continue
        actual_kind = "dir" if os.path.isdir(target) and not os.path.islink(target) else "file"
        candidates.append(Candidate(
            kind=actual_kind, ref=rel, key=fs_key(root_real, rel),
            evidence="profile", size_bytes=size_of(target, notes)))
    walked_rels = [rel for rel, _mtime in walk_dirs] + walk_files
    for _raw_pattern, compiled in profile.clean_globs:
        for rel in walked_rels:
            if compiled.fullmatch(rel) is None:
                continue
            target = os.path.join(root, rel)
            actual_kind = "dir" if os.path.isdir(target) and not os.path.islink(target) else "file"
            candidates.append(Candidate(
                kind=actual_kind, ref=rel, key=fs_key(root_real, rel),
                evidence="profile", size_bytes=size_of(target, notes)))
    return candidates


def docker_run(root: str, args: list[str]) -> tuple[int, str, str]:
    proc = run_capture(["docker"] + args, root)
    return (proc.returncode,
            proc.stdout.decode("utf-8", errors="replace"),
            proc.stderr.decode("utf-8", errors="replace"))


def inspect_ref(root: str, ref: str, kind: str, slug: str) -> tuple[str, str, str, str]:
    if kind == "container":
        fmt = ('{{.ID}}\\t{{.State.Status}}\\t{{index .Labels "'
               + INSPECT_LABEL_KEY + '"}}')
        scope = "container"
    else:
        fmt = '{{.ID}}\\t{{index .Config.Labels "' + INSPECT_LABEL_KEY + '"}}'
        scope = "image"
    rc, out, err = docker_run(root, [scope, "inspect", ref, "--format", fmt])
    if rc != 0:
        if "No such object" in err:
            return "gone", "", "", ""
        return "error", "", first_line(err), ""
    lines = out.splitlines()
    line = lines[0] if lines else ""
    parts = line.split("\t")
    if not parts[0]:
        return "error", "", "empty inspect output", ""
    if kind == "container":
        if len(parts) < 3:
            return "error", "", "unexpected inspect output", ""
        return "ok", parts[0], parts[1], parts[2]
    if len(parts) < 2:
        return "error", "", "unexpected inspect output", ""
    return "ok", parts[0], "", parts[1]


def slug_in_name(name: str, slug: str, patterns: list[str]) -> bool:
    if slug and slug in name:
        return True
    return any(fnmatchcase(name, pattern) for pattern in patterns)


def docker_layer(root: str, slug: str, profile: ProfileData,
                 notes: list[str]) -> tuple[dict, list[Candidate]]:
    section: dict = {"available": False, "cli": "absent", "labeled": [], "naming_ambiguous": []}
    if shutil.which("docker") is None:
        notes.append(NOTE_DOCKER_ABSENT)
        return section, []
    section["available"] = True
    labeled: list[dict] = []
    naming: list[dict] = []
    candidates: list[Candidate] = []
    healthy = True
    rc, out, err = docker_run(root, [
        "ps", "-a", "--filter", f"label={DOCKER_LABEL_KEY}{slug}", "--format", PS_FORMAT])
    labeled_ids: set[str] = set()
    if rc != 0:
        healthy = False
        notes.append(f"docker unavailable: {first_line(err)}")
    else:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            labeled_ids.add(parts[0])
            labeled.append({"kind": "container", "id": parts[0], "name": parts[1],
                            "detail": parts[2]})
            if not status_is_running(parts[2]) and not docker_status_stopped(parts[2]):
                notes.append(
                    f"docker container skipped (unknown status): {parts[0]} ({parts[2]})")
                continue
            candidates.append(Candidate(
                kind="container", ref=parts[0], key=f"docker:{parts[0]}",
                evidence="docker-label", docker_status=parts[2]))
    rc, out, err = docker_run(root, ["ps", "-a", "--format", PS_FORMAT])
    if rc != 0:
        healthy = False
        notes.append(f"docker unavailable: {first_line(err)}")
    else:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 3 or parts[0] in labeled_ids:
                continue
            if slug_in_name(parts[1], slug, profile.docker_names):
                naming.append({"kind": "container", "id": parts[0], "name": parts[1],
                               "detail": parts[2]})
                candidates.append(Candidate(
                    kind="container", ref=parts[0], key=f"docker:{parts[0]}",
                    evidence="docker-naming", docker_status=parts[2]))
    rc, out, err = docker_run(root, [
        "images", "--filter", f"label={DOCKER_LABEL_KEY}{slug}", "--format", IMAGE_FORMAT])
    labeled_image_ids: set[str] = set()
    if rc != 0:
        healthy = False
        notes.append(f"docker unavailable: {first_line(err)}")
    else:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            name = f"{parts[1]}:{parts[2]}" if parts[2] not in ("", "<none>") else parts[1]
            labeled_image_ids.add(parts[0])
            labeled.append({"kind": "image", "id": parts[0], "name": name,
                            "detail": parts[3]})
            candidates.append(Candidate(
                kind="image", ref=parts[0], key=f"docker:{parts[0]}", evidence="docker-label"))
    rc, out, err = docker_run(root, ["images", "--format", IMAGE_FORMAT])
    if rc != 0:
        healthy = False
        notes.append(f"docker unavailable: {first_line(err)}")
    else:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 4 or parts[0] in labeled_image_ids:
                continue
            name = f"{parts[1]}:{parts[2]}" if parts[2] not in ("", "<none>") else parts[1]
            if slug_in_name(name, slug, profile.docker_names):
                naming.append({"kind": "image", "id": parts[0], "name": name,
                               "detail": parts[3]})
                candidates.append(Candidate(
                    kind="image", ref=parts[0], key=f"docker:{parts[0]}",
                    evidence="docker-naming"))
    section["cli"] = "ok" if healthy else "error"
    section["labeled"] = labeled
    section["naming_ambiguous"] = naming
    return section, candidates


def stack_layer(root: str, root_real: str, stacks: list[str],
                walk_dirs: list[tuple[str, float]], notes: list[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    walked = [rel for rel, _mtime in walk_dirs]
    for stack in stacks:
        for pattern in STACK_DERIVATIONS.get(stack, []):
            anchored = pattern.rstrip("/")
            for rel in walked:
                if not fnmatchcase(rel, anchored):
                    continue
                target = os.path.join(root, rel)
                candidates.append(Candidate(
                    kind="dir", ref=rel, key=fs_key(root_real, rel),
                    evidence="stack-derived", pattern=pattern,
                    size_bytes=size_of(target, notes)))
    return candidates


def shape_layer(root: str, root_real: str, walk_dirs: list[tuple[str, float]],
                min_size_mb: int, git_ok: bool, head_ts: int | None,
                notes: list[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    threshold = min_size_mb * 1024 * 1024
    for rel, mtime in walk_dirs:
        name = rel.rsplit("/", 1)[-1]
        if not shape_name_matches(name):
            continue
        target = os.path.join(root, rel)
        size = size_of(target, notes)
        if size < threshold:
            continue
        if not freshness_ok(root, rel, mtime, git_ok, head_ts, notes):
            continue
        candidates.append(Candidate(
            kind="dir", ref=rel, key=fs_key(root_real, rel),
            evidence="shape-sign", size_bytes=size))
    return candidates


def extra_layer(root: str, root_real: str, extras: list[str],
                notes: list[str]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for raw in extras:
        candidate_path = raw if os.path.isabs(raw) else os.path.join(root, raw)
        rel = normalize_rel(os.path.relpath(candidate_path, root))
        if not rel:
            notes.append(f"extra path resolves to the project root: {raw}")
            continue
        if is_red_line(rel):
            candidates.append(Candidate(
                kind="dir", ref=rel, key=fs_key(root_real, rel), evidence="agent"))
            continue
        if not os.path.exists(candidate_path):
            notes.append(f"extra path not found: {raw}")
            continue
        actual_kind = "dir" if os.path.isdir(candidate_path) and not os.path.islink(candidate_path) else "file"
        candidates.append(Candidate(
            kind=actual_kind, ref=rel, key=fs_key(root_real, rel),
            evidence="agent", size_bytes=size_of(candidate_path, notes)))
    return candidates


def refusal_reason(gates: list[str]) -> str:
    for reason in REFUSAL_ORDER:
        if reason in gates:
            return reason
    return ""


def classify(evidence: str, gates: list[str]) -> str:
    if refusal_reason(gates):
        return "refused"
    if evidence in CLEAR_EVIDENCE:
        return "ambiguous" if "tracked-unknown" in gates else "clear"
    if evidence in AMBIGUOUS_EVIDENCE:
        return "ambiguous"
    return "ambiguous"


def candidate_gates(candidate: Candidate, root: str, root_real: str,
                    git_ok: bool) -> tuple[list[str], str]:
    if candidate.kind in ("container", "image"):
        gates = ["running-container"] if status_is_running(candidate.docker_status) else []
        return gates, "untracked"
    gates: list[str] = []
    if is_red_line(candidate.ref):
        gates.append("red-line")
        return gates, "untracked"
    reason = containment_reason(root_real, candidate.ref)
    if reason:
        gates.append(reason)
        return gates, "untracked"
    tracked = tracked_state(git_ok, root, candidate.ref)
    if tracked == "tracked":
        gates.append("tracked-files")
    elif tracked == "unknown":
        gates.append("tracked-unknown")
    return gates, tracked


def rebuild_text(candidate: Candidate, profile: ProfileData) -> str:
    if candidate.pattern in REBUILD_HINTS:
        return REBUILD_HINTS[candidate.pattern]
    if candidate.kind in ("container", "image"):
        return REBUILD_RUNNING
    for compiled, hint in profile.rebuild_globs:
        if compiled.fullmatch(candidate.ref) is not None:
            return hint
    return REBUILD_GENERIC


def why_ambiguous(evidence: str, gates: list[str]) -> str:
    if "tracked-unknown" in gates and evidence in CLEAR_EVIDENCE:
        return "tracked-file gate unavailable (no usable git history here)"
    if evidence == "shape-sign":
        return "disposable-shape name matched without stack or profile evidence"
    if evidence == "docker-naming":
        return "name suggests this project but the object carries no project label"
    if evidence == "agent":
        return "agent-provided candidate: only the owner can confirm it"
    return "ownership not proven"


def evaluate_candidates(candidates: list[Candidate], root: str, root_real: str,
                        git_ok: bool, profile: ProfileData, kept_paths: list[str],
                        notes: list[str]) -> tuple[list[dict], list[dict], list[dict], list[str], int]:
    ordered = sorted(candidates, key=lambda candidate: EVIDENCE_RANK[candidate.evidence])
    seen: set[str] = set()
    clear_entries: list[dict] = []
    ambiguous_entries: list[dict] = []
    refused_entries: list[dict] = []
    excluded_report: list[str] = []
    examined = 0
    for candidate in ordered:
        if candidate.key in seen:
            continue
        seen.add(candidate.key)
        examined += 1
        gates, tracked = candidate_gates(candidate, root, root_real, git_ok)
        reason = refusal_reason(gates)
        if reason:
            refused_entries.append({"ref": candidate.ref, "reason": reason})
            if candidate.evidence == "profile":
                notes.append(f"profile clean target refused: {candidate.ref} ({reason})")
            continue
        if candidate.kind in ("dir", "file") and is_kept(candidate.ref, profile):
            if candidate.ref not in excluded_report:
                excluded_report.append(candidate.ref)
            continue
        if candidate.kind == "dir" and contains_kept(candidate.ref, kept_paths):
            notes.append(f"candidate skipped: a keep= path lives inside it: {candidate.ref}")
            continue
        disposition = classify(candidate.evidence, gates)
        rebuild = rebuild_text(candidate, profile)
        if disposition == "clear":
            clear_entries.append({
                "ref": candidate.ref,
                "kind": candidate.kind,
                "evidence": candidate.evidence,
                "size_bytes": candidate.size_bytes,
                "rebuild": rebuild,
                "tracked_any": tracked == "tracked",
            })
        else:
            ambiguous_entries.append({
                "ref": candidate.ref,
                "kind": candidate.kind,
                "evidence": candidate.evidence,
                "size_bytes": candidate.size_bytes,
                "rebuild": rebuild,
                "why_ambiguous": why_ambiguous(candidate.evidence, gates),
            })
    return clear_entries, ambiguous_entries, refused_entries, excluded_report, examined


def build_plan(root: str, min_size_mb: int, extras: list[str]) -> dict:
    notes: list[str] = []
    root_real = os.path.realpath(root)
    slug = sanitize_slug(os.path.basename(root_real) or "project")
    git_ok, git_reason = git_repo_state(root)
    if not git_ok:
        notes.append(
            f"git unavailable ({git_reason}): freshness uses mtime only, "
            "tracked-file gate answered as unknown")
    head_ts = commit_timestamp(root, "") if git_ok else None
    stacks = detect_stacks(root)
    profile = parse_profile(root, notes)
    manifests = manifest_paths(root)
    kept_paths: list[str] = []
    walk_dirs, walk_files = walk_tree(root, profile, kept_paths, notes)
    candidates: list[Candidate] = []
    candidates += stack_layer(root, root_real, stacks, walk_dirs, notes)
    candidates += shape_layer(root, root_real, walk_dirs, min_size_mb, git_ok, head_ts, notes)
    candidates += manifest_layer(root, root_real, slug, notes)
    candidates += profile_layer(root, root_real, walk_dirs, walk_files, profile, notes)
    docker_section, docker_candidates = docker_layer(root, slug, profile, notes)
    candidates += docker_candidates
    candidates += extra_layer(root, root_real, extras, notes)
    clear_entries, ambiguous_entries, refused_entries, excluded_report, examined = (
        evaluate_candidates(candidates, root, root_real, git_ok, profile, kept_paths, notes))
    return {
        "mode": "dry-run",
        "project_root": root_real,
        "slug": slug,
        "stacks_detected": stacks,
        "accelerators": {
            "manifest": "; ".join(manifests) if manifests else "absent",
            "profile": profile.path if profile.path else "absent",
        },
        "docker": docker_section,
        "clear": sorted(clear_entries, key=lambda entry: entry["ref"]),
        "ambiguous": sorted(ambiguous_entries, key=lambda entry: entry["ref"]),
        "refused": sorted(refused_entries, key=lambda entry: entry["ref"]),
        "excluded_by_profile": sorted(set(excluded_report + kept_paths)),
        "notes": list(dict.fromkeys(notes)),
        "totals": {
            "candidates_examined": examined,
            "clear_bytes": sum(entry["size_bytes"] for entry in clear_entries),
            "ambiguous_bytes": sum(entry["size_bytes"] for entry in ambiguous_entries),
        },
    }


def read_apply_source(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    try:
        with open(source, encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise UsageError(f"apply plan unreadable: {source} ({exc.strerror})") from exc


def validate_apply_plan(plan: object, root_real: str) -> list[dict]:
    if not isinstance(plan, dict):
        raise UsageError("apply plan is not a JSON object")
    if plan.get("confirmed") is not True:
        raise UsageError('apply plan is not confirmed: the "confirmed" field must be true')
    declared_root = plan.get("project_root")
    if not isinstance(declared_root, str) or not declared_root:
        raise UsageError("apply plan is missing a string project_root")
    if os.path.realpath(declared_root) != root_real:
        raise UsageError("apply plan project_root does not match --root")
    entries = plan.get("clear", [])
    if not isinstance(entries, list):
        raise UsageError('apply plan has no valid "clear" section')
    targets: list[dict] = []
    for entry in entries:
        if (isinstance(entry, dict) and isinstance(entry.get("ref"), str)
                and isinstance(entry.get("kind"), str)):
            if "owner_approved" in entry and not isinstance(entry.get("owner_approved"), bool):
                raise UsageError("apply plan owner_approved must be a boolean")
            targets.append(entry)
        else:
            raise UsageError("apply plan clear entries must be objects with string ref and kind")
    return targets


def apply_fs_target(root: str, root_real: str, entry: dict[str, str], git_ok: bool,
                    removed: list[dict], skipped: list[dict], failed: list[dict],
                    already_gone: list[str], notes: list[str]) -> None:
    raw_ref = entry["ref"]
    kind = entry["kind"]
    if os.path.isabs(raw_ref):
        candidate_abs = os.path.normpath(raw_ref)
        resolved = os.path.realpath(candidate_abs)
        if resolved != root_real and not resolved.startswith(root_real + os.sep):
            skipped.append({"ref": raw_ref, "kind": kind, "reason": "outside-project"})
            return
        rel = normalize_rel(os.path.relpath(candidate_abs, root))
    else:
        rel = normalize_rel(raw_ref)
    if not rel:
        skipped.append({"ref": raw_ref, "kind": kind, "reason": "invalid-ref"})
        return
    if is_red_line(rel):
        skipped.append({"ref": rel, "kind": kind, "reason": "red-line"})
        return
    reason = containment_reason(root_real, rel)
    if reason:
        skipped.append({"ref": rel, "kind": kind, "reason": reason})
        return
    target = os.path.join(root, rel)
    tracked = tracked_state(git_ok, root, rel)
    if tracked == "tracked":
        skipped.append({"ref": rel, "kind": kind, "reason": "tracked-files"})
        return
    if tracked == "unknown":
        skipped.append({"ref": rel, "kind": kind, "reason": "tracked-unknown"})
        notes.append(f"tracked-file gate unavailable at apply: {rel}")
        return
    if not os.path.exists(target) and not os.path.islink(target):
        already_gone.append(rel)
        notes.append(f"already gone: {rel}")
        return
    try:
        if os.path.islink(target) or not os.path.isdir(target):
            os.unlink(target)
        else:
            shutil.rmtree(target)
    except OSError as exc:
        failed.append({"ref": rel, "kind": kind, "error": exc.strerror or str(exc)})
        return
    removed.append({"ref": rel, "kind": kind})


def apply_docker_target(root: str, slug: str, entry: dict, docker_present: bool,
                        removed: list[dict], skipped: list[dict], failed: list[dict],
                        already_gone: list[str], notes: list[str]) -> None:
    ref = entry["ref"]
    kind = entry["kind"]
    if not docker_present:
        skipped.append({"ref": ref, "kind": kind, "reason": "docker-unavailable"})
        notes.append(f"docker unavailable at apply: {ref} skipped")
        return
    state, object_id, status, label_value = inspect_ref(root, ref, kind, slug)
    if state == "gone":
        already_gone.append(ref)
        notes.append(f"already gone: {ref}")
        return
    if state == "error":
        skipped.append({"ref": ref, "kind": kind, "reason": "docker-unavailable"})
        notes.append(f"docker unavailable: {status}")
        return
    if kind == "container" and status_is_running(status):
        skipped.append({"ref": ref, "kind": kind, "reason": "running-container"})
        return
    if kind == "container" and not docker_status_stopped(status):
        skipped.append({"ref": ref, "kind": kind, "reason": "unknown-container-status"})
        notes.append(f"docker target status is not verifiably stopped at apply: {ref} ({status})")
        return
    if label_value != slug:
        if label_value or entry.get("owner_approved") is not True:
            skipped.append({"ref": ref, "kind": kind, "reason": "not-project-labeled"})
            notes.append(f"docker target not labeled {INSPECT_LABEL_KEY}={slug}: {ref}")
            return
    action = "rm" if kind == "container" else "rmi"
    rc, _out, err = docker_run(root, [action, object_id])
    if rc != 0:
        failed.append({"ref": ref, "kind": kind, "error": first_line(err)})
        return
    removed.append({"ref": ref, "kind": kind})


def apply_plan(root: str, source: str) -> int:
    root_real = os.path.realpath(root)
    slug = sanitize_slug(os.path.basename(root_real) or "project")
    raw = read_apply_source(source)
    try:
        plan = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UsageError(f"apply plan is not valid JSON: {exc.msg}") from exc
    targets = validate_apply_plan(plan, root_real)
    notes: list[str] = []
    removed: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    already_gone: list[str] = []
    git_ok, _reason = git_repo_state(root)
    docker_present = shutil.which("docker") is not None
    containers = [entry for entry in targets if entry["kind"] == "container"]
    images = [entry for entry in targets if entry["kind"] == "image"]
    fs_targets = [entry for entry in targets if entry["kind"] in ("dir", "file")]
    for entry in targets:
        if entry["kind"] not in ("dir", "file", "container", "image"):
            skipped.append({"ref": entry["ref"], "kind": entry["kind"], "reason": "unknown-kind"})
    for entry in containers:
        apply_docker_target(root, slug, entry, docker_present, removed, skipped, failed,
                            already_gone, notes)
    for entry in images:
        apply_docker_target(root, slug, entry, docker_present, removed, skipped, failed,
                            already_gone, notes)
    for entry in fs_targets:
        apply_fs_target(root, root_real, entry, git_ok, removed, skipped, failed,
                        already_gone, notes)
    report = {
        "mode": "apply",
        "project_root": root_real,
        "removed": removed,
        "skipped": skipped,
        "failed": failed,
        "already_gone": already_gone,
        "notes": list(dict.fromkeys(notes)),
        "totals": {
            "planned": len(targets),
            "removed": len(removed),
            "skipped": len(skipped),
            "failed": len(failed),
        },
    }
    print(json.dumps(report, indent=2))
    return 1 if skipped or failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cleanup_scan.py",
        description="Deterministic post-epic artifact cleanup scan/plan/apply core.")
    parser.add_argument("--root", required=True, metavar="PROJECT_ROOT",
                        help="project root directory")
    parser.add_argument("--min-size-mb", type=int, default=10, metavar="N",
                        help="size threshold in MB for shape-sign candidates (default 10)")
    parser.add_argument("--extra", nargs="+", default=[], metavar="PATH",
                        help="extra candidate paths proposed by the agent")
    parser.add_argument("--apply", default=None, metavar="FILE",
                        help="apply a confirmed JSON plan from FILE ('-' reads stdin)")
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"error: project root does not exist or is not a directory: {args.root}",
              file=sys.stderr)
        sys.exit(USAGE_EXIT)
    try:
        if args.apply is not None:
            sys.exit(apply_plan(root, args.apply))
        print(json.dumps(build_plan(root, args.min_size_mb, args.extra), indent=2))
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(USAGE_EXIT)
    sys.exit(0)


if __name__ == "__main__":
    main()
