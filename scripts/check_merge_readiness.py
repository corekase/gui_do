#!/usr/bin/env python3
"""Check whether gui_do files can be safely copied into an existing project.

Checks performed against the target project directory:

1. Package name collisions -- looks for existing `gui_do/` directory
   in the target project that would conflict with the same-named package from
   gui_do.
2. Demo test file name conflicts -- lists any files in the target's `tests/`
   directory that share a name with demo test files that `bootstrap new` deletes.

Usage:
    python scripts/check_merge_readiness.py --target PATH

    PATH is the root directory of the existing project you plan to copy
    gui_do files into.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


CORE_PACKAGES = ("gui_do",)

DEMO_TEST_NAMES = (
    "test_bouncing_shapes_demo_feature.py",
    "test_controls_demo_feature.py",
    "test_demo_features_gui_portability.py",
    "test_feature_lifecycle_host_parameter_contracts.py",
    "test_gui_do_demo_life_runtime.py",
    "test_gui_do_demo_presentation_model.py",
    "test_mandel_event_schema_exports.py",
    "test_mandel_logic_feature_runtime.py",
    "test_styles_demo_feature.py",
)


def _check_package_collisions(target: Path) -> tuple[list[str], list[str]]:
    """Return (collisions, messages) by checking for existing package directories."""
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
    """Return (conflicts, messages) by checking the target tests/ directory."""
    tests_dir = target / "tests"
    conflicts = []
    messages = []
    for name in DEMO_TEST_NAMES:
        existing = tests_dir / name
        if existing.exists():
            conflicts.append(str(existing.relative_to(target)))
            messages.append(f"  CONFLICT: {existing.relative_to(target)}")
    return conflicts, messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether gui_do files can be safely copied into an existing project directory."
        )
    )
    parser.add_argument(
        "--target",
        required=True,
        metavar="PATH",
        help="Root directory of the existing project to check.",
    )
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"[check-merge] ERROR: target directory not found: {target}", file=sys.stderr)
        return 2

    print(f"[check-merge] target project: {target}\n")

    issues: list[str] = []

    # 1. Package name collisions.
    print("--- Package name collisions ---")
    collisions, msgs = _check_package_collisions(target)
    for msg in msgs:
        print(msg)
    issues.extend(f"package collision: {pkg}" for pkg in collisions)
    print()

    # 2. Demo test file name conflicts.
    print("--- Demo test file name conflicts ---")
    conflicts, msgs = _check_demo_test_conflicts(target)
    if conflicts:
        print(
            "  NOTE: The following files exist in the target and share a name with demo test\n"
            "  files that `bootstrap new` deletes. Rename them before running bootstrap:\n"
        )
        for msg in msgs:
            print(msg)
    else:
        print("  OK: No demo test file name conflicts in target project.")
    print()

    # Summary.
    if issues:
        print(f"[check-merge] {len(issues)} issue(s) require attention before merging:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("[check-merge] All checks passed. Safe to proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
