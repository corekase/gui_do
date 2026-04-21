"""Shared parsing helpers for contract documentation tests."""

import re
from pathlib import Path


def section_body(text: str, heading: str, source_name: str) -> str:
    start = text.find(heading)
    if start == -1:
        raise AssertionError(f"{source_name} missing '{heading}' section")
    section = text[start + len(heading):]
    next_heading = section.find("\n## ")
    if next_heading != -1:
        section = section[:next_heading]
    return section


def commands_from_fenced_section(
    text: str,
    heading: str,
    source_name: str,
    fence_language: str = "bash",
) -> list[str]:
    section = section_body(text, heading, source_name)
    fence_start = section.find(f"```{fence_language}")
    if fence_start == -1:
        raise AssertionError(f"{source_name} section '{heading}' missing {fence_language} code fence")
    section = section[fence_start + len(f"```{fence_language}"):]
    fence_end = section.find("```")
    if fence_end == -1:
        raise AssertionError(f"{source_name} section '{heading}' missing closing code fence")
    code_block = section[:fence_end]

    commands = []
    for raw_line in code_block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        commands.append(line)
    return commands


def readme_boundary_commands(repo_root: Path) -> list[str]:
    text = (repo_root / "README.md").read_text(encoding="utf-8")
    return commands_from_fenced_section(text, "## Run Boundary Contract Tests", "README", fence_language="bash")


def backticked_bullet_items(section_text: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(r"^-\s+`([^`]+)`.*$", section_text, flags=re.MULTILINE)
    ]


def workflow_step_run_command(repo_root: Path, step_name: str) -> str:
    workflow_text = (repo_root / ".github" / "workflows" / "unittest.yml").read_text(encoding="utf-8")
    return workflow_step_run_command_from_text(workflow_text, step_name)


def workflow_step_names(repo_root: Path) -> list[str]:
    workflow_text = (repo_root / ".github" / "workflows" / "unittest.yml").read_text(encoding="utf-8")
    return workflow_step_names_from_text(workflow_text)


def workflow_step_names_from_text(workflow_text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^\s*-\s*name:\s*(.+?)\s*$", workflow_text, flags=re.MULTILINE)
    ]


def workflow_step_run_command_from_text(workflow_text: str, step_name: str) -> str:
    target = f"- name: {step_name}"
    start = workflow_text.find(target)
    if start == -1:
        raise AssertionError(f"workflow missing '{step_name}' step")

    section = workflow_text[start:]
    next_step_match = re.search(r"\n\s*-\s*name:\s+", section[len(target):])
    if next_step_match is not None:
        next_step_index = len(target) + next_step_match.start()
        section = section[:next_step_index]

    run_marker = "run: "
    run_index = section.find(run_marker)
    if run_index == -1:
        raise AssertionError(f"workflow step '{step_name}' missing run command")
    run_line = section[run_index + len(run_marker):].splitlines()[0].rstrip()

    stripped = run_line.strip()
    if stripped == "|":
        block_lines = []
        for candidate in section[run_index + len(run_marker):].splitlines()[1:]:
            if not candidate.startswith("        "):
                break
            block_lines.append(candidate.strip())

        for line in block_lines:
            if line and not line.startswith("#"):
                return line
        raise AssertionError(f"workflow step '{step_name}' run block is empty")

    if not stripped:
        raise AssertionError(f"workflow step '{step_name}' run command is empty")
    return stripped
