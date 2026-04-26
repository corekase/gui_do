#!/usr/bin/env python3
"""Manage gui_do projects from either the current folder or a source-to-target copy flow.

Current-folder commands:
- init: convert the current folder into a starter project
- apply: apply required project updates to the current folder
- verify: run the contract verification command for the current folder

Source-to-target commands:
- check: validate a target project before copying gui_do into it
- update: copy this source folder into --target and apply required project updates there
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

DEMO_TEST_DISCOVERY_RULE = "any test file in tests/ that imports from demo_features"

DEFAULT_SCAFFOLD_FILE = "myapp.py"
DEFAULT_SCAFFOLD_PACKAGE = "features"

SYNC_DIRS = (
    "gui_do",
    "scripts",
    "tests",
    "docs",
)

SYNC_FILES = (
    "README.md",
    "pyproject.toml",
    "MANIFEST.in",
    "LICENSE",
    "requirements-ci.txt",
)

CORE_PACKAGES = ("gui_do",)


def _find_demo_test_files(root: Path) -> list[Path]:
    """Return all test files in root/tests/ that import from demo_features."""
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        return []
    results = []
    for test_file in sorted(tests_dir.glob("test_*.py")):
        try:
            text = test_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if re.search(r"^(?:from|import) demo_features\b", text, re.MULTILINE):
            results.append(test_file)
    return results


def _replace_optional(text: str, old: str, new: str) -> tuple[str, bool]:
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def _set_demo_contracts_disabled(catalog_text: str, file_label: str) -> tuple[str, bool]:
    pattern = re.compile(r"^DEMO_CONTRACTS_ENABLED\s*=\s*(True|False)\s*$", flags=re.MULTILINE)
    match = pattern.search(catalog_text)
    if not match:
        raise RuntimeError(f"Missing DEMO_CONTRACTS_ENABLED assignment in {file_label}")
    current = match.group(1)
    if current == "False":
        return catalog_text, False
    updated = pattern.sub("DEMO_CONTRACTS_ENABLED = False", catalog_text, count=1)
    return updated, True


def _update_section(text: str, heading: str, replacement_body: str, file_label: str) -> str:
    pattern = re.compile(rf"({re.escape(heading)}\n)([\s\S]*?)(?=\n## |\Z)")
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Missing section {heading} in {file_label}")
    return text[: match.start()] + match.group(1) + replacement_body.rstrip() + "\n\n" + text[match.end() :]


def _write(path: Path, content: str, apply: bool) -> None:
    if apply:
        path.write_text(content, encoding="utf-8", newline="\n")


def _delete_path(path: Path, apply: bool) -> None:
    if not path.exists():
        return
    if apply:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def _read_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _check_package_collisions(target: Path) -> tuple[list[str], list[str]]:
    collisions = []
    messages = []
    for pkg in CORE_PACKAGES:
        existing = target / pkg
        if existing.exists():
            collisions.append(pkg)
            messages.append(
                f"  COLLISION: `{pkg}/` already exists in target project ({existing}).\n"
                f"  Rename one of them before copying gui_do files in."
            )
        else:
            messages.append(f"  OK: no `{pkg}/` in target project.")
    return collisions, messages


def _check_demo_test_conflicts(target: Path) -> tuple[list[str], list[str]]:
    """Identify demo test files in the target that would be deleted by update+apply."""
    conflicts = []
    messages = []
    for test_file in _find_demo_test_files(target):
        rel = str(test_file.relative_to(target))
        conflicts.append(rel)
        messages.append(f"  CONFLICT: {rel}")
    return conflicts, messages


def _run_merge_readiness_check(target: Path) -> int:
    if not target.is_dir():
        print(f"[check] ERROR: target directory not found: {target}")
        return 2

    print(f"[check] target project: {target}\n")
    issues: list[str] = []

    print("--- Package name collisions ---")
    collisions, msgs = _check_package_collisions(target)
    for msg in msgs:
        print(msg)
    issues.extend(f"package collision: {pkg}" for pkg in collisions)
    print()

    print("--- Demo test file name conflicts ---")
    conflicts, msgs = _check_demo_test_conflicts(target)
    if conflicts:
        print(
            "  NOTE: The following files exist in the target and share a name with demo test\n"
            "  files that setup sync deletes. Rename them before running update:\n"
        )
        for msg in msgs:
            print(msg)
    else:
        print("  OK: No demo test file name conflicts in target project.")
    print()

    if issues:
        print(f"[check] {len(issues)} issue(s) require attention before update:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("[check] All checks passed. Safe to proceed.")
    return 0


def _copy_dir(src: Path, dst: Path, apply: bool) -> None:
    if not src.exists():
        return
    if apply:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    print(f"[update] {'copied' if apply else 'would copy'} directory: {src.name}")


def _copy_file(src: Path, dst: Path, apply: bool) -> None:
    if not src.exists():
        return
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"[update] {'copied' if apply else 'would copy'} file: {src.name}")


def _run_merge_upgrade(
    source_root: Path,
    *,
    target: Path,
    apply: bool,
    verify: bool,
    skip_doc_sync: bool,
    skip_workflow_sync: bool,
) -> int:
    if not target.is_dir():
        print(f"[update] ERROR: target directory not found: {target}")
        return 2

    print(f"[update] source: {source_root}")
    print(f"[update] target: {target}")
    print(f"[update] mode: {'apply' if apply else 'dry-run'}")

    for rel in SYNC_DIRS:
        _copy_dir(source_root / rel, target / rel, apply)

    for rel in SYNC_FILES:
        _copy_file(source_root / rel, target / rel, apply)

    if not apply:
        print("[update] dry-run complete (no files changed)")
        return 0

    bootstrap_path = target / "scripts" / "manage.py"
    if not bootstrap_path.exists():
        print("[update] ERROR: target is missing scripts/manage.py after copy.")
        return 2

    cmd = ["python", str(bootstrap_path), "apply"]
    if skip_doc_sync:
        cmd.append("--skip-doc-sync")
    if skip_workflow_sync:
        cmd.append("--skip-workflow-sync")
    if verify:
        cmd.append("--verify")

    print("[update] running target sync:", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(target), check=False)
    return int(completed.returncode)


def _core_only_catalog_values(catalog_path: Path) -> dict[str, object]:
    source = catalog_path.read_text(encoding="utf-8-sig")
    source, _ = _set_demo_contracts_disabled(source, str(catalog_path))
    namespace: dict[str, object] = {}
    exec(compile(source, str(catalog_path), "exec"), namespace)
    return namespace


def _sync_core_only(
    root: Path,
    *,
    apply: bool,
    skip_doc_sync: bool,
    skip_workflow_sync: bool,
) -> dict[str, object]:
    print(f"[bootstrap] mode: {'apply' if apply else 'dry-run'}")

    catalog_path = root / "tests" / "contract_test_catalog.py"
    catalog_text = catalog_path.read_text(encoding="utf-8")
    catalog_text, changed_mode = _set_demo_contracts_disabled(catalog_text, str(catalog_path))
    _write(catalog_path, catalog_text, apply)
    if changed_mode:
        print("[bootstrap] set DEMO_CONTRACTS_ENABLED = False")
    else:
        print("[bootstrap] DEMO_CONTRACTS_ENABLED already False")

    catalog_values = _core_only_catalog_values(catalog_path)
    unittest_cmd = catalog_values["CONTRACT_UNITTEST_COMMAND"]
    pytest_cmd = catalog_values["CONTRACT_PYTEST_COMMAND"]
    boundary_pytest_cmd = catalog_values["BOUNDARY_PYTEST_COMMAND"]
    boundary_tests = catalog_values["BOUNDARY_ENFORCEMENT_TEST_IDS"]

    if not skip_doc_sync:
        package_contracts_path = root / "docs" / "package_contracts.md"
        package_contracts_text = _read_if_exists(package_contracts_path)
        if package_contracts_text is None:
            print("[bootstrap] skipped package contracts sync (docs/package_contracts.md not found)")
        else:
            package_contracts_text = _update_section(
                package_contracts_text,
                "## Run Boundary Contract Tests",
                "```bash\n"
                f"{unittest_cmd}\n"
                f"{boundary_pytest_cmd}\n"
                f"{pytest_cmd}\n"
                "```",
                str(package_contracts_path),
            )
            _write(package_contracts_path, package_contracts_text, apply)
            print("[bootstrap] updated package contracts boundary commands")

        boundary_spec_path = root / "docs" / "architecture_boundary_spec.md"
        boundary_spec_text = _read_if_exists(boundary_spec_path)
        if boundary_spec_text is None:
            print("[bootstrap] skipped architecture boundary doc sync (file not found)")
        else:
            enforcement_body = "Automated tests enforce both directions:\n\n" + "\n".join(
                f"- `{test_id}`" for test_id in boundary_tests
            ) + "\n\nThe boundary test uses AST-based import inspection, so only real imports are flagged (not comments or strings).\n\nRun command:\n\n```bash\npython -m pytest -q tests/test_boundary_contracts.py\n```"

            boundary_spec_text = _update_section(
                boundary_spec_text,
                "## Current Demo Boundary Assets",
                "No demo boundary assets in core-only starter mode.",
                str(boundary_spec_path),
            )
            boundary_spec_text = _update_section(
                boundary_spec_text,
                "## Current Active Demo Entrypoints",
                "No demo entrypoints in core-only starter mode.",
                str(boundary_spec_path),
            )
            boundary_spec_text = _update_section(
                boundary_spec_text,
                "## Enforcement",
                enforcement_body,
                str(boundary_spec_path),
            )
            _write(boundary_spec_path, boundary_spec_text, apply)
            print("[bootstrap] updated architecture boundary spec")

        public_api_spec_path = root / "docs" / "public_api_spec.md"
        public_api_spec_text = _read_if_exists(public_api_spec_path)
        if public_api_spec_text is None:
            print("[bootstrap] skipped public API doc sync (file not found)")
        else:
            public_api_spec_text, removed_demo_test_ref = _replace_optional(
                public_api_spec_text,
                "- `tests/test_mandel_event_schema_exports.py`\n",
                "",
            )
            _write(public_api_spec_path, public_api_spec_text, apply)
            if removed_demo_test_ref:
                print("[bootstrap] updated public API enforced test list")
            else:
                print("[bootstrap] public API enforced test list already core-only")
    else:
        print("[bootstrap] skipped README/docs sync (--skip-doc-sync)")

    if not skip_workflow_sync:
        workflow_path = root / ".github" / "workflows" / "unittest.yml"
        workflow_text = _read_if_exists(workflow_path)
        if workflow_text is None:
            print("[bootstrap] skipped workflow sync (.github/workflows/unittest.yml not found)")
        else:
            workflow_text, count = re.subn(
                r"(\n\s*- name: Run boundary contract tests\n\s*run: ).*",
                rf"\1{unittest_cmd}",
                workflow_text,
                count=1,
            )
            if count != 1:
                raise RuntimeError("Could not update boundary test step in .github/workflows/unittest.yml")
            _write(workflow_path, workflow_text, apply)
            print("[bootstrap] updated workflow boundary command")
    else:
        print("[bootstrap] skipped workflow sync (--skip-workflow-sync)")

    _delete_path(root / "gui_do_demo.py", apply)
    _delete_path(root / "demo_features", apply)
    for test_file in _find_demo_test_files(root):
        _delete_path(test_file, apply)
    print("[bootstrap] removed demo entrypoint, demo_features package, and demo-specific tests")

    if apply:
        print("[bootstrap] sync complete")
    else:
        print("[bootstrap] check complete (no files changed)")

    return catalog_values


def _scaffold_starter(root: Path, *, apply: bool, app_file: str, package_name: str) -> None:
    app_path = root / app_file
    package_path = root / package_name
    init_path = package_path / "__init__.py"
    feature_path = package_path / "starter_feature.py"

    app_content = """import pygame
from pygame import Rect

from gui_do import GuiApplication, PanelControl, LabelControl, ButtonControl


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption(\"gui_do app\")

    app = GuiApplication(screen)
    app.create_scene(\"main\")
    app.switch_scene(\"main\")

    root = app.add(
        PanelControl(\"root\", Rect(0, 0, screen.get_width(), screen.get_height())),
        scene_name=\"main\",
    )
    root.add(LabelControl(\"hello\", Rect(20, 20, 520, 32), \"Hello from your gui_do project\"))
    root.add(ButtonControl(\"quit\", Rect(20, 64, 140, 32), \"Quit\", on_click=app.quit))

    app.run(target_fps=60)
    pygame.quit()


if __name__ == \"__main__\":
    main()
"""

    feature_content = """from gui_do import Feature


class StarterFeature(Feature):
    def __init__(self) -> None:
        super().__init__(\"starter_feature\", scene_name=\"main\")
"""

    if app_path.exists():
        print(f"[bootstrap] skipped scaffold file (already exists): {app_file}")
    else:
        if apply:
            app_path.write_text(app_content, encoding="utf-8", newline="\n")
        print(f"[bootstrap] {'created' if apply else 'would create'} scaffold app file: {app_file}")

    if package_path.exists():
        print(f"[bootstrap] skipped scaffold package (already exists): {package_name}")
    else:
        if apply:
            package_path.mkdir(parents=True, exist_ok=True)
            init_path.write_text("", encoding="utf-8", newline="\n")
            feature_path.write_text(feature_content, encoding="utf-8", newline="\n")
        print(f"[bootstrap] {'created' if apply else 'would create'} scaffold package: {package_name}")


def _run_verification(root: Path, catalog_values: dict[str, object]) -> int:
    command = str(catalog_values["CONTRACT_UNITTEST_COMMAND"])
    print(f"[bootstrap] running verification: {command}")
    completed = subprocess.run(command, cwd=str(root), shell=True, check=False)
    return int(completed.returncode)


def _resolve_mode(args: argparse.Namespace) -> tuple[str, bool]:
    command = args.command
    if command is None:
        if args.apply:
            return "apply", True
        return "help", False

    if command in ("verify", "check"):
        return command, False
    # command must be "init", "apply", or "update" — the only remaining choices
    return command, not args.dry_run

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        nargs="?",
        choices=("init", "apply", "verify", "check", "update"),
    )

    # Backward-compatibility flag: legacy callers used --apply with no subcommand.
    parser.add_argument("--apply", action="store_true", help="Legacy: apply required project updates to the current folder")

    parser.add_argument("--dry-run", action="store_true", help="Preview file changes without writing")
    parser.add_argument("--target", help="Target project root (required for check and update; relative paths are resolved from your shell's current working directory)")
    parser.add_argument("--skip-doc-sync", action="store_true", help="Do not rewrite README/docs parity sections")
    parser.add_argument("--skip-workflow-sync", action="store_true", help="Do not rewrite CI workflow command")
    parser.add_argument("--verify", action="store_true", help="Run contract verification after init, apply, or update")
    parser.add_argument("--scaffold", action="store_true", help="Create starter app scaffolding during init")
    parser.add_argument("--scaffold-file", default=DEFAULT_SCAFFOLD_FILE, help="Scaffold app entrypoint file path")
    parser.add_argument("--scaffold-package", default=DEFAULT_SCAFFOLD_PACKAGE, help="Scaffold package directory")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    mode, apply = _resolve_mode(args)

    if mode == "help":
        parser.print_help()
        return 0

    if mode == "verify":
        return _run_verification(root, _core_only_catalog_values(root / "tests" / "contract_test_catalog.py"))

    if mode == "check":
        if not args.target:
            parser.error("--target is required for check")
        return _run_merge_readiness_check(Path(args.target).resolve())

    if mode == "update":
        if not args.target:
            parser.error("--target is required for update")
        return _run_merge_upgrade(
            root,
            target=Path(args.target).resolve(),
            apply=apply,
            verify=args.verify,
            skip_doc_sync=args.skip_doc_sync,
            skip_workflow_sync=args.skip_workflow_sync,
        )

    catalog_values = _sync_core_only(
        root,
        apply=apply,
        skip_doc_sync=args.skip_doc_sync,
        skip_workflow_sync=args.skip_workflow_sync,
    )

    if mode == "init" and args.scaffold:
        _scaffold_starter(
            root,
            apply=apply,
            app_file=args.scaffold_file,
            package_name=args.scaffold_package,
        )

    if args.verify and apply:
        return _run_verification(root, catalog_values)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
