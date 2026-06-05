#!/usr/bin/env python3
"""Create and optionally deploy a clean docs source release package.

The package is built from Git indexes, not from a raw filesystem copy:

- the main repository contributes only `git ls-files` entries;
- each skill submodule contributes only its own `git ls-files` entries;
- ignored/runtime files such as `.tmp/`, `node_modules/`, and local caches are
  therefore excluded by construction.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import pathlib
import posixpath
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DEPLOY_PATH = "/opt/mozhi-agent-workspace-docs"
DEFAULT_REMOTE_TMP = "/tmp/mozhi-agent-workspace-releases"
EXCLUDED_MAIN_PREFIXES = (".git/",)
EXCLUDED_MAIN_FILES = {".git"}


@dataclass(frozen=True)
class RepoFile:
    source: pathlib.Path
    arcname: str


def run(
    args: list[str],
    *,
    cwd: pathlib.Path = ROOT,
    capture: bool = False,
    check: bool = True,
) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=False,
        text=False,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and result.returncode != 0:
        if capture:
            sys.stderr.write(result.stderr.decode("utf-8", errors="replace"))
        raise SystemExit(result.returncode)
    if not capture:
        return ""
    return result.stdout.decode("utf-8", errors="replace")


def ensure_clean() -> None:
    status = run(["git", "status", "--porcelain"], capture=True)
    if status.strip():
        raise SystemExit(
            "Working tree is not clean. Commit or stash changes before creating a release.\n"
            + status
        )


def git_output(args: list[str], cwd: pathlib.Path = ROOT) -> str:
    return run(["git", *args], cwd=cwd, capture=True).strip()


def git_files(repo: pathlib.Path) -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=repo)
    return [item.decode("utf-8") for item in raw.split(b"\0") if item]


def submodule_paths() -> list[str]:
    gitmodules = ROOT / ".gitmodules"
    if not gitmodules.exists():
        return []
    output = run(
        ["git", "config", "--file", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"],
        capture=True,
        check=False,
    )
    paths: list[str] = []
    for line in output.splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            paths.append(parts[1].replace("\\", "/"))
    return paths


def collect_files() -> list[RepoFile]:
    submodules = set(submodule_paths())
    files: list[RepoFile] = []

    for rel in git_files(ROOT):
        normalized = rel.replace("\\", "/")
        if normalized in submodules:
            continue
        if normalized in EXCLUDED_MAIN_FILES or normalized.startswith(EXCLUDED_MAIN_PREFIXES):
            continue
        source = ROOT / normalized
        if source.is_file():
            files.append(RepoFile(source=source, arcname=normalized))

    for submodule in sorted(submodules):
        repo = ROOT / submodule
        if not repo.exists():
            raise SystemExit(f"Submodule path does not exist: {submodule}")
        for rel in git_files(repo):
            normalized = rel.replace("\\", "/")
            source = repo / normalized
            if source.is_file():
                files.append(
                    RepoFile(
                        source=source,
                        arcname=posixpath.join(submodule, normalized),
                    )
                )

    return sorted(files, key=lambda item: item.arcname)


def create_tag(tag: str, message: str, push_tag: bool) -> None:
    existing = run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], capture=True, check=False)
    if existing.strip():
        print(f"[tag] existing tag: {tag}")
    else:
        run(["git", "tag", "-a", tag, "-m", message])
        print(f"[tag] created: {tag}")
    if push_tag:
        run(["git", "push", "origin", tag])
        print(f"[tag] pushed: {tag}")


def release_metadata(tag: str) -> str:
    lines = [
        f"tag: {tag}",
        f"created_at_utc: {dt.datetime.now(dt.UTC).isoformat()}",
        f"main_commit: {git_output(['rev-parse', 'HEAD'])}",
        "",
        "submodules:",
    ]
    for path in submodule_paths():
        sha = git_output(["rev-parse", "HEAD"], cwd=ROOT / path)
        lines.append(f"- {path}: {sha}")
    lines.append("")
    return "\n".join(lines)


def create_package(tag: str, output_dir: pathlib.Path) -> pathlib.Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_tag = tag.replace("/", "-")
    package = output_dir / f"mozhi-agent-workspace-{safe_tag}.tar.gz"
    top_dir = f"mozhi-agent-workspace-{safe_tag}"
    files = collect_files()

    with tarfile.open(package, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        for item in files:
            tar.add(item.source, arcname=posixpath.join(top_dir, item.arcname), recursive=False)

        metadata = release_metadata(tag).encode("utf-8")
        info = tarfile.TarInfo(posixpath.join(top_dir, "RELEASE.txt"))
        info.size = len(metadata)
        info.mtime = int(dt.datetime.now(dt.UTC).timestamp())
        tar.addfile(info, io.BytesIO(metadata))

    print(f"[package] {package}")
    print(f"[package] tracked files: {len(files)}")
    return package


def remote_install_script(package_name: str, deploy_path: str, remote_tmp: str) -> str:
    package_path = posixpath.join(remote_tmp, package_name)
    return f"""set -euo pipefail
DEPLOY_PATH={sh_quote(deploy_path)}
PACKAGE={sh_quote(package_path)}
WORKDIR=$(mktemp -d /tmp/mozhi-agent-workspace-release.XXXXXX)
trap 'rm -rf "$WORKDIR"' EXIT
tar -xzf "$PACKAGE" -C "$WORKDIR"
SRC=$(find "$WORKDIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
test -n "$SRC"
test -f "$SRC/compose.docs.yml"
PARENT=$(dirname "$DEPLOY_PATH")
mkdir -p "$PARENT"
rm -rf "$DEPLOY_PATH"
mv "$SRC" "$DEPLOY_PATH"
cd "$DEPLOY_PATH"
docker compose -f compose.docs.yml restart docs
docker compose -f compose.docs.yml ps
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8888/ -o /dev/null && \
     curl -fsS http://127.0.0.1:8888/skill-static/ppt-deep-search/showcase/rtx-spark-agent-pc/review/source_understanding_review.htm -o /dev/null; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "docs service did not become ready in time" >&2
    exit 1
  fi
  sleep 2
done
echo "deployed package: $PACKAGE"
"""


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def deploy_package(package: pathlib.Path, remote: str, deploy_path: str, remote_tmp: str) -> None:
    run(["ssh", remote, f"mkdir -p {sh_quote(remote_tmp)}"], cwd=ROOT)
    remote_package = f"{remote}:{posixpath.join(remote_tmp, package.name)}"
    run(["scp", str(package), remote_package], cwd=ROOT)
    script = remote_install_script(package.name, deploy_path, remote_tmp)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, suffix=".sh") as handle:
        handle.write(script)
        script_path = pathlib.Path(handle.name)
    try:
        run(["scp", str(script_path), f"{remote}:{posixpath.join(remote_tmp, 'install-release.sh')}"], cwd=ROOT)
        run(["ssh", remote, f"bash {sh_quote(posixpath.join(remote_tmp, 'install-release.sh'))}"], cwd=ROOT)
    finally:
        script_path.unlink(missing_ok=True)


def default_tag() -> str:
    return "docs-" + dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and optionally deploy a docs source release package.")
    parser.add_argument("--tag", default=default_tag(), help="release tag to create/use")
    parser.add_argument("--message", default=None, help="annotated tag message")
    parser.add_argument("--push-tag", action="store_true", help="push the tag to origin")
    parser.add_argument("--output-dir", default=str(ROOT / ".tmp" / "releases"), help="local package output directory")
    parser.add_argument("--remote", help="remote SSH target, for example root@39.105.78.135")
    parser.add_argument("--deploy-path", default=DEFAULT_DEPLOY_PATH, help="remote docs source directory")
    parser.add_argument("--remote-tmp", default=DEFAULT_REMOTE_TMP, help="remote directory for uploaded packages")
    parser.add_argument("--skip-tag", action="store_true", help="create package without creating a tag")
    parser.add_argument("--push-tag-only-if-deploy", action="store_true", help="push tag only when --remote is set")
    parser.add_argument("--allow-dirty", action="store_true", help="allow packaging from a dirty working tree")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.allow_dirty:
        ensure_clean()

    message = args.message or f"Docs release {args.tag}"
    if not args.skip_tag:
        push_tag = args.push_tag or (args.push_tag_only_if_deploy and bool(args.remote))
        create_tag(args.tag, message, push_tag)

    package = create_package(args.tag, pathlib.Path(args.output_dir).resolve())
    if args.remote:
        deploy_package(package, args.remote, args.deploy_path, args.remote_tmp)


if __name__ == "__main__":
    main()
