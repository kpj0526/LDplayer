"""Regression tests: generated logs/diagnostics artifacts must be
git-ignored, and existing config protection must be untouched."""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_ignored(relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", relative_path],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    return result.returncode == 0


@pytest.mark.parametrize(
    "relative_path",
    [
        "logs/LD1/task.log",
        "logs/LD5/error.log",
        "diagnostics/screenshots/LD1/2026-01-01.png",
        "diagnostics/screenshots/LD9/meta.json",
    ],
)
def test_generated_artifact_paths_are_gitignored(relative_path):
    assert _is_ignored(relative_path), f"{relative_path} should be git-ignored"


def test_config_yaml_is_still_gitignored():
    assert _is_ignored("configs/config.yaml")


def test_config_example_yaml_is_not_ignored():
    # The tracked template must remain trackable.
    assert not _is_ignored("configs/config.example.yaml")


def test_mission_yaml_is_gitignored():
    assert _is_ignored("configs/mission.yaml")


def test_mission_example_yaml_is_not_ignored():
    assert not _is_ignored("configs/mission.example.yaml")


def test_bounty_yaml_is_gitignored():
    assert _is_ignored("configs/bounty.yaml")


def test_bounty_example_yaml_is_not_ignored():
    assert not _is_ignored("configs/bounty.example.yaml")


@pytest.mark.parametrize("relative_path", ["build/ldmanager/ldmanager.exe", "dist/ldmanager.exe", "ldmanager.spec"])
def test_pyinstaller_build_artifacts_are_gitignored(relative_path):
    assert _is_ignored(relative_path), f"{relative_path} should be git-ignored"


def test_source_files_are_not_accidentally_ignored():
    assert not _is_ignored("src/ldmanager/logs.py")
