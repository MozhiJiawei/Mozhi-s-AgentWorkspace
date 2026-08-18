#!/usr/bin/env python3
"""Package and operate the AgentWorkspace resource-server deployment."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
from pathlib import Path
import posixpath
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[3]
DEPLOY_ROOT = ROOT / "deploy" / "resource-server"
CCN_SOURCE_ROOT = ROOT / "loops" / "ccn-brief-report" / "task_service"
DEFAULT_REMOTE = "root@39.105.78.135"
DEFAULT_DEPLOY_PATH = "/opt/mozhi-agent-workspace-services"
DEFAULT_REMOTE_TMP = "/tmp/mozhi-agent-workspace-releases"
EDGE_SOURCE_FILES = (
    "deploy/resource-server/compose.production.yml",
    "deploy/resource-server/edge/Caddyfile.template",
    "deploy/resource-server/edge/Dockerfile",
    "deploy/resource-server/edge/entrypoint.sh",
    "deploy/resource-server/scripts/update-edge-source.sh",
)


def run(args: list[str], *, cwd: Path = ROOT, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode:
        if capture:
            sys.stderr.write(result.stderr.decode("utf-8", errors="replace"))
        raise SystemExit(result.returncode)
    return result.stdout.decode("utf-8", errors="replace") if capture else ""


def ensure_clean() -> None:
    status = run(["git", "status", "--porcelain"], capture=True)
    if status.strip():
        raise SystemExit("Working tree is not clean. Commit or use --allow-dirty.\n" + status)


def ensure_paths_clean(paths: tuple[str, ...]) -> None:
    dirty = run(["git", "status", "--porcelain", "--", *paths], capture=True)
    if dirty.strip():
        raise SystemExit("Edge 发布文件存在未提交改动：\n" + dirty)


def git_files(repo: Path, *, include_untracked: bool = False) -> list[str]:
    command = ["git", "ls-files", "-z", "--cached"]
    if include_untracked:
        command.extend(["--others", "--exclude-standard"])
    raw = subprocess.check_output(command, cwd=repo)
    return [part.decode("utf-8") for part in raw.split(b"\0") if part]


def submodule_paths() -> list[str]:
    if not (ROOT / ".gitmodules").exists():
        return []
    output = run(
        ["git", "config", "--file", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"],
        capture=True,
    )
    return [line.split(maxsplit=1)[1].replace("\\", "/") for line in output.splitlines() if " " in line]


def package_files(*, include_untracked: bool = False) -> list[tuple[Path, str]]:
    submodules = set(submodule_paths())
    files: list[tuple[Path, str]] = []
    for rel in git_files(ROOT, include_untracked=include_untracked):
        normalized = rel.replace("\\", "/")
        if normalized in submodules or normalized == ".git":
            continue
        source = ROOT / normalized
        if source.is_file():
            files.append((source, normalized))
    for submodule in sorted(submodules):
        repo = ROOT / submodule
        for rel in git_files(repo):
            normalized = rel.replace("\\", "/")
            source = repo / normalized
            if source.is_file():
                files.append((source, posixpath.join(submodule, normalized)))
    return sorted(files, key=lambda item: item[1])


def create_package(output_dir: Path, label: str, *, include_untracked: bool = False) -> Path:
    required = [
        DEPLOY_ROOT / "compose.production.yml",
        DEPLOY_ROOT / "scripts" / "install.sh",
        ROOT / "loops" / "ccn-brief-report" / "task_service" / "app" / "main.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required deployment files: " + ", ".join(missing))
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
    package = output_dir / f"mozhi-resource-server-{label}-{timestamp}.tar.gz"
    top = f"mozhi-resource-server-{label}-{timestamp}"
    files = package_files(include_untracked=include_untracked)
    with tarfile.open(package, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for source, arcname in files:
            archive.add(source, arcname=posixpath.join(top, arcname), recursive=False)
        metadata = (
            f"created_at_utc: {dt.datetime.now(dt.UTC).isoformat()}\n"
            f"main_commit: {run(['git', 'rev-parse', 'HEAD'], capture=True).strip()}\n"
        ).encode()
        info = tarfile.TarInfo(posixpath.join(top, "RELEASE.txt"))
        info.size = len(metadata)
        archive.addfile(info, io.BytesIO(metadata))
    print(package)
    return package


def create_ccn_source_package(output_dir: Path) -> Path:
    required = [
        CCN_SOURCE_ROOT / "pyproject.toml",
        CCN_SOURCE_ROOT / "alembic.ini",
        DEPLOY_ROOT / "compose.production.yml",
        DEPLOY_ROOT / "scripts" / "update-ccn-source.sh",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required CCN source files: " + ", ".join(missing))
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
    package = output_dir / f"mozhi-resource-server-ccn-source-{timestamp}.tar.gz"
    top = f"mozhi-resource-server-ccn-source-{timestamp}"
    source_files = [
        path for path in CCN_SOURCE_ROOT.rglob("*")
        if path.is_file()
        and not any(part in {"__pycache__", ".pytest_cache", "ccn_brief_task_service.egg-info"} for part in path.parts)
        and path.suffix not in {".pyc", ".pyo"}
    ]
    source_files.extend(
        [DEPLOY_ROOT / "compose.production.yml", DEPLOY_ROOT / "scripts" / "update-ccn-source.sh"]
    )
    with tarfile.open(package, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for source in sorted(source_files):
            relative = source.relative_to(ROOT).as_posix()
            archive.add(source, arcname=posixpath.join(top, relative), recursive=False)
    print(package)
    return package


def create_edge_source_package(output_dir: Path) -> Path:
    ensure_paths_clean(EDGE_SOURCE_FILES)
    missing = [relative for relative in EDGE_SOURCE_FILES if not (ROOT / relative).is_file()]
    if missing:
        raise SystemExit("Missing required edge source files: " + ", ".join(missing))
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
    package = output_dir / f"mozhi-resource-server-edge-source-{timestamp}.tar.gz"
    top = f"mozhi-resource-server-edge-source-{timestamp}"
    with tarfile.open(package, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        for relative in EDGE_SOURCE_FILES:
            archive.add(ROOT / relative, arcname=posixpath.join(top, relative), recursive=False)
    print(package)
    return package


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_remote_upload_dir(remote: str, remote_tmp: str) -> None:
    quoted = sh_quote(remote_tmp)
    run(["ssh", remote, f"install -d -m 700 {quoted} && chown 0:0 {quoted}"])


def deploy(package: Path, remote: str, deploy_path: str, remote_tmp: str, component: str) -> None:
    remote_package = posixpath.join(remote_tmp, package.name)
    expected_sha256 = sha256_file(package)
    prepare_remote_upload_dir(remote, remote_tmp)
    run(["scp", str(package), f"{remote}:{remote_package}"])
    command = (
        f"package={sh_quote(remote_package)} && "
        f"actual=$(sha256sum \"$package\" | awk '{{print $1}}') && "
        f"[ \"$actual\" = {sh_quote(expected_sha256)} ] && "
        f"tmp=$(mktemp -d /tmp/mozhi-resource-install.XXXXXX) && "
        f"trap 'rm -rf \"$tmp\"; rm -f \"$package\"' EXIT && "
        f"tar -xzf \"$package\" -C \"$tmp\" && "
        f"src=$(find \"$tmp\" -mindepth 1 -maxdepth 1 -type d | head -n 1) && "
        f"DEPLOY_PATH={sh_quote(deploy_path)} COMPONENT={sh_quote(component)} bash "
        f"\"$src/deploy/resource-server/scripts/install.sh\" \"$src\""
    )
    run(["ssh", remote, command])


def deploy_ccn_source(
    package: Path,
    remote: str,
    deploy_path: str,
    remote_tmp: str,
    *,
    bootstrap_mount: bool,
) -> None:
    remote_package = posixpath.join(remote_tmp, package.name)
    expected_sha256 = sha256_file(package)
    prepare_remote_upload_dir(remote, remote_tmp)
    run(["scp", str(package), f"{remote}:{remote_package}"])
    bootstrap = "true" if bootstrap_mount else "false"
    command = (
        f"package={sh_quote(remote_package)} && "
        f"actual=$(sha256sum \"$package\" | awk '{{print $1}}') && "
        f"[ \"$actual\" = {sh_quote(expected_sha256)} ] && "
        f"tmp=$(mktemp -d /tmp/mozhi-ccn-source.XXXXXX) && "
        f"trap 'rm -rf \"$tmp\"; rm -f \"$package\"' EXIT && "
        f"tar -xzf \"$package\" -C \"$tmp\" && "
        f"src=$(find \"$tmp\" -mindepth 1 -maxdepth 1 -type d | head -n 1) && "
        f"DEPLOY_PATH={sh_quote(deploy_path)} BOOTSTRAP_MOUNT={bootstrap} bash "
        f"\"$src/deploy/resource-server/scripts/update-ccn-source.sh\" \"$src\""
    )
    run(["ssh", remote, command])


def deploy_edge_source(package: Path, remote: str, deploy_path: str, remote_tmp: str) -> None:
    remote_package = posixpath.join(remote_tmp, package.name)
    expected_sha256 = sha256_file(package)
    prepare_remote_upload_dir(remote, remote_tmp)
    run(["scp", str(package), f"{remote}:{remote_package}"])
    command = (
        f"package={sh_quote(remote_package)} && "
        f"actual=$(sha256sum \"$package\" | awk '{{print $1}}') && "
        f"[ \"$actual\" = {sh_quote(expected_sha256)} ] && "
        f"tmp=$(mktemp -d /tmp/mozhi-edge-source.XXXXXX) && "
        f"trap 'rm -rf \"$tmp\"; rm -f \"$package\"' EXIT && "
        f"tar -xzf \"$package\" -C \"$tmp\" && "
        f"src=$(find \"$tmp\" -mindepth 1 -maxdepth 1 -type d | head -n 1) && "
        f"DEPLOY_PATH={sh_quote(deploy_path)} bash "
        f"\"$src/deploy/resource-server/scripts/update-edge-source.sh\" \"$src\""
    )
    run(["ssh", remote, command])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-dirty", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    package = sub.add_parser("package")
    package.add_argument("--label", default="manual")
    package.add_argument("--output-dir", default=str(ROOT / ".tmp" / "releases"))

    deploy_parser = sub.add_parser("deploy")
    deploy_parser.add_argument("--component", choices=["docs", "ccn", "edge", "all"], default="all")
    deploy_parser.add_argument("--remote", default=DEFAULT_REMOTE)
    deploy_parser.add_argument("--deploy-path", default=DEFAULT_DEPLOY_PATH)
    deploy_parser.add_argument("--remote-tmp", default=DEFAULT_REMOTE_TMP)
    deploy_parser.add_argument("--output-dir", default=str(ROOT / ".tmp" / "releases"))

    source_deploy = sub.add_parser("deploy-ccn-source")
    source_deploy.add_argument("--remote", default=DEFAULT_REMOTE)
    source_deploy.add_argument("--deploy-path", default=DEFAULT_DEPLOY_PATH)
    source_deploy.add_argument("--remote-tmp", default=DEFAULT_REMOTE_TMP)
    source_deploy.add_argument("--output-dir", default=str(ROOT / ".tmp" / "releases"))
    source_deploy.add_argument("--bootstrap-mount", action="store_true")

    edge_source = sub.add_parser("deploy-edge-source")
    edge_source.add_argument("--remote", default=DEFAULT_REMOTE)
    edge_source.add_argument("--deploy-path", default=DEFAULT_DEPLOY_PATH)
    edge_source.add_argument("--remote-tmp", default=DEFAULT_REMOTE_TMP)
    edge_source.add_argument("--output-dir", default=str(ROOT / ".tmp" / "releases"))

    smoke = sub.add_parser("smoke-test")
    smoke.add_argument("--api-base", default="https://ccn-api.haohaoxiaoyu.top")
    smoke.add_argument("--docs-base", default="https://docs.haohaoxiaoyu.top")
    smoke.add_argument("--api-key")
    smoke.add_argument("--internal", action="store_true")
    smoke.add_argument("--skip-write", action="store_true")

    rollback = sub.add_parser("rollback")
    rollback.add_argument("--remote", default=DEFAULT_REMOTE)
    rollback.add_argument("--deploy-path", default=DEFAULT_DEPLOY_PATH)
    rollback.add_argument("--component", choices=["docs", "ccn", "edge", "all"], default="all")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command in {"package", "deploy", "deploy-ccn-source"} and not args.allow_dirty:
        ensure_clean()
    if args.command == "package":
        create_package(
            Path(args.output_dir).resolve(),
            args.label,
            include_untracked=args.allow_dirty,
        )
    elif args.command == "deploy":
        package = create_package(
            Path(args.output_dir).resolve(),
            args.component,
            include_untracked=args.allow_dirty,
        )
        deploy(package, args.remote, args.deploy_path, args.remote_tmp, args.component)
    elif args.command == "deploy-ccn-source":
        package = create_ccn_source_package(Path(args.output_dir).resolve())
        deploy_ccn_source(
            package,
            args.remote,
            args.deploy_path,
            args.remote_tmp,
            bootstrap_mount=args.bootstrap_mount,
        )
    elif args.command == "deploy-edge-source":
        package = create_edge_source_package(Path(args.output_dir).resolve())
        deploy_edge_source(package, args.remote, args.deploy_path, args.remote_tmp)
    elif args.command == "smoke-test":
        command = [
            sys.executable,
            str(DEPLOY_ROOT / "scripts" / "smoke-test.py"),
            "--api-base",
            args.api_base,
            "--docs-base",
            args.docs_base,
        ]
        if args.api_key:
            command.extend(["--api-key", args.api_key])
        if args.internal:
            command.append("--internal")
        if args.skip_write:
            command.append("--skip-write")
        run(command)
    else:
        remote_script = posixpath.join(args.deploy_path, "deploy/resource-server/scripts/rollback.sh")
        run(
            [
                "ssh",
                args.remote,
                f"DEPLOY_PATH={sh_quote(args.deploy_path)} COMPONENT={sh_quote(args.component)} "
                f"bash {sh_quote(remote_script)}",
            ]
        )


if __name__ == "__main__":
    main()
