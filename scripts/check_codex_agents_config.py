from __future__ import annotations

import argparse
import configparser
from dataclasses import dataclass
from pathlib import Path
import posixpath
import shutil
import sys
import tempfile
import textwrap
import tomllib


CONFIG_PATH = Path(".codex/config.toml")
AGENT_GLOB = ".codex/agents/*.toml"


@dataclass(frozen=True)
class SkillAgent:
    name: str
    description: str
    developer_instructions: str
    path: Path


@dataclass(frozen=True)
class ConfigAgent:
    name: str
    description: str
    config_file: str


def parse_gitmodule_skill_paths(root: Path) -> list[str]:
    gitmodules_path = root / ".gitmodules"
    if not gitmodules_path.exists():
        return []

    parser = configparser.ConfigParser()
    parser.read(gitmodules_path, encoding="utf-8")
    paths: list[str] = []
    for section in parser.sections():
        if parser.has_option(section, "path"):
            path = parser.get(section, "path").strip().replace("\\", "/")
            if path.startswith("skills/"):
                paths.append(path)
    return sorted(paths)


def read_toml(path: Path) -> tuple[dict[str, object] | None, str | None]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"Missing file: {path.as_posix()}"
    except tomllib.TOMLDecodeError as exc:
        return None, f"Invalid TOML in {path.as_posix()}: {exc}"
    except UnicodeDecodeError as exc:
        return None, f"Cannot read {path.as_posix()} as UTF-8: {exc}"


def required_string(data: dict[str, object], key: str, path: Path) -> tuple[str | None, str | None]:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        return None, f"{path.as_posix()}: missing required string field `{key}`"
    return value, None


def discover_skill_agents(root: Path) -> tuple[list[SkillAgent], list[str]]:
    errors: list[str] = []
    agents: list[SkillAgent] = []
    seen: dict[str, Path] = {}

    for skill_path in parse_gitmodule_skill_paths(root):
        skill_root = root / skill_path
        for agent_path in sorted(skill_root.glob(AGENT_GLOB)):
            data, error = read_toml(agent_path)
            if error:
                errors.append(error)
                continue
            assert data is not None

            name, name_error = required_string(data, "name", agent_path)
            description, description_error = required_string(data, "description", agent_path)
            developer_instructions, developer_error = required_string(
                data, "developer_instructions", agent_path
            )
            for field_error in (name_error, description_error, developer_error):
                if field_error:
                    errors.append(field_error)
            if not name or not description or developer_instructions is None:
                continue

            previous = seen.get(name)
            if previous is not None:
                errors.append(
                    "Duplicate Codex agent name "
                    f"`{name}` in {previous.relative_to(root).as_posix()} and "
                    f"{agent_path.relative_to(root).as_posix()}"
                )
                continue
            seen[name] = agent_path
            agents.append(
                SkillAgent(
                    name=name,
                    description=description,
                    developer_instructions=developer_instructions,
                    path=agent_path,
                )
            )

    return sorted(agents, key=lambda agent: agent.name), errors


def parse_config_agents(config_path: Path) -> tuple[dict[str, ConfigAgent], dict[str, object] | None, list[str]]:
    data, error = read_toml(config_path)
    if error:
        return {}, None, [error]
    assert data is not None

    errors: list[str] = []
    raw_agents = data.get("agents", {})
    if raw_agents is None:
        raw_agents = {}
    if not isinstance(raw_agents, dict):
        return {}, data, ["`.codex/config.toml` field `agents` must be a table"]

    agents: dict[str, ConfigAgent] = {}
    for name, raw in raw_agents.items():
        if not isinstance(raw, dict):
            errors.append(f"[agents.{name}] must be a table")
            continue
        description = raw.get("description")
        config_file = raw.get("config_file")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"[agents.{name}] missing required string field `description`")
            continue
        if not isinstance(config_file, str) or not config_file.strip():
            errors.append(f"[agents.{name}] missing required string field `config_file`")
            continue
        agents[name] = ConfigAgent(name=name, description=description, config_file=config_file)

    return agents, data, errors


def expected_config_file(root: Path, agent_path: Path) -> str:
    config_dir = (root / CONFIG_PATH).parent
    relative = posixpath.relpath(agent_path.relative_to(root).as_posix(), config_dir.relative_to(root).as_posix())
    return relative


def resolves_under_skills(root: Path, config_file: str) -> bool:
    config_dir = (root / CONFIG_PATH).parent
    try:
        resolved = (config_dir / config_file).resolve()
        skills_root = (root / "skills").resolve()
        return resolved == skills_root or skills_root in resolved.parents
    except OSError:
        normalized = config_file.replace("\\", "/")
        return normalized.startswith("../skills/") or normalized.startswith("skills/")


def validate_config(root: Path, agents: list[SkillAgent]) -> list[str]:
    config_path = root / CONFIG_PATH
    config_agents, _, errors = parse_config_agents(config_path)
    if errors:
        return errors

    skill_agents = {agent.name: agent for agent in agents}
    for agent in agents:
        configured = config_agents.get(agent.name)
        expected_file = expected_config_file(root, agent.path)
        relative_agent_path = agent.path.relative_to(root).as_posix()
        if configured is None:
            errors.append(
                f"Missing [agents.{agent.name}] for {relative_agent_path}; run "
                "`python scripts/check_codex_agents_config.py --update`."
            )
            continue
        if configured.description != agent.description:
            errors.append(
                f"[agents.{agent.name}] description differs from {relative_agent_path}; "
                "run `python scripts/check_codex_agents_config.py --update`."
            )
        if configured.config_file != expected_file:
            errors.append(
                f"[agents.{agent.name}] config_file must be `{expected_file}`, "
                f"found `{configured.config_file}`."
            )
        configured_path = (config_path.parent / configured.config_file).resolve()
        if not configured_path.is_file():
            errors.append(
                f"[agents.{agent.name}] config_file target does not exist: "
                f"{configured.config_file}"
            )

    for name, configured in sorted(config_agents.items()):
        if name in skill_agents:
            continue
        if resolves_under_skills(root, configured.config_file):
            errors.append(
                f"Orphaned skill Codex agent [agents.{name}] points to "
                f"`{configured.config_file}` but no matching skill agent was discovered."
            )

    return errors


def toml_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\b", "\\b")
        .replace("\f", "\\f")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def render_agent_block(agent: SkillAgent, root: Path) -> str:
    return "\n".join(
        [
            f"[agents.{agent.name}]",
            f"description = {toml_string(agent.description)}",
            f"config_file = {toml_string(expected_config_file(root, agent.path))}",
            "",
        ]
    )


def render_preserved_agent_block(name: str, raw: dict[str, object]) -> str:
    lines = [f"[agents.{name}]"]
    for key in sorted(raw):
        value = raw[key]
        if isinstance(value, str):
            lines.append(f"{key} = {toml_string(value)}")
        elif isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        elif isinstance(value, int) and not isinstance(value, bool):
            lines.append(f"{key} = {value}")
        elif isinstance(value, float):
            lines.append(f"{key} = {value}")
        else:
            raise ValueError(f"Cannot preserve [agents.{name}] field `{key}` with non-scalar value")
    lines.append("")
    return "\n".join(lines)


def update_config(root: Path, agents: list[SkillAgent]) -> list[str]:
    config_path = root / CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)

    preserved_blocks: list[str] = []
    if config_path.exists():
        config_agents, data, errors = parse_config_agents(config_path)
        if errors:
            return errors
        assert data is not None
        raw_agents = data.get("agents", {})
        assert isinstance(raw_agents, dict)
        for name in sorted(config_agents):
            configured = config_agents[name]
            if resolves_under_skills(root, configured.config_file):
                continue
            raw = raw_agents.get(name)
            if isinstance(raw, dict):
                try:
                    preserved_blocks.append(render_preserved_agent_block(name, raw))
                except ValueError as exc:
                    return [str(exc)]

    content_parts: list[str] = []
    content_parts.extend(preserved_blocks)
    content_parts.extend(render_agent_block(agent, root) for agent in agents)
    config_path.write_text("\n".join(content_parts).rstrip() + "\n", encoding="utf-8")
    return []


def run_check(root: Path, update: bool) -> int:
    agents, discover_errors = discover_skill_agents(root)
    if discover_errors:
        for error in discover_errors:
            print(error)
        return 1

    if update:
        update_errors = update_config(root, agents)
        if update_errors:
            for error in update_errors:
                print(error)
            return 1
        print(f"Updated {CONFIG_PATH.as_posix()} with {len(agents)} skill Codex agent(s).")
        return 0

    errors = validate_config(root, agents)
    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"Codex agents config check passed for {len(agents)} skill agent(s).")
    return 0


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def run_self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file(
            root / ".gitmodules",
            """
            [submodule "skills/example"]
                path = skills/example
                url = https://example.invalid/example.git
            """,
        )
        write_file(
            root / "skills/example/.codex/agents/foo.toml",
            '''
            name = "foo"
            description = "Foo agent."
            developer_instructions = """
            Do foo.
            """
            ''',
        )

        if run_check(root, update=False) == 0:
            print("[self-test] expected missing config to fail")
            return 1
        if run_check(root, update=True) != 0:
            print("[self-test] expected update to pass")
            return 1
        if run_check(root, update=False) != 0:
            print("[self-test] expected updated config to pass")
            return 1

        write_file(
            root / "skills/example/.codex/agents/bar.toml",
            '''
            name = "bar"
            description = "Bar agent."
            developer_instructions = "Do bar."
            ''',
        )
        if run_check(root, update=False) == 0:
            print("[self-test] expected missing second agent to fail")
            return 1

        shutil.rmtree(root / "skills/example/.codex/agents")
        write_file(
            root / "skills/example/.codex/agents/a.toml",
            '''
            name = "dup"
            description = "A."
            developer_instructions = "A."
            ''',
        )
        write_file(
            root / "skills/example/.codex/agents/b.toml",
            '''
            name = "dup"
            description = "B."
            developer_instructions = "B."
            ''',
        )
        if run_check(root, update=False) == 0:
            print("[self-test] expected duplicate names to fail")
            return 1

    print("[self-test] check_codex_agents_config scenarios passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that root .codex/config.toml matches skill Codex agents."
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Rewrite skill-backed [agents.*] entries in .codex/config.toml from subrepo agent TOML files.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in check scenarios in a temporary workspace.",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    root = Path(__file__).resolve().parent.parent
    return run_check(root, update=args.update)


if __name__ == "__main__":
    raise SystemExit(main())
