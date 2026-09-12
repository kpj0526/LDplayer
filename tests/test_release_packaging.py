"""Release packaging regression tests (REL-0.1.0-PKG-01).

Does not invoke PyInstaller (too slow/heavy for the regular suite) --
verifies the build script's packaging step is present in source, and
that the source files it packages actually exist, so a future edit
can't silently regress "the ZIP has no configs" again without a test
failing. An actual PyInstaller build + launch of the resulting exe was
additionally performed manually in the delivering session -- see
docs/HANDOFF_CODE.md's REL-0.1.0-PKG-01 section for that account.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_windows.ps1"


def test_build_script_exists():
    assert BUILD_SCRIPT.is_file()


def test_build_script_copies_example_configs_into_dist():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert 'configs\\config.example.yaml' in text
    assert 'configs\\bounty.example.yaml' in text
    assert '$DistRoot\\configs' in text


def test_build_script_copies_templates_into_dist():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert '$DistRoot\\templates' in text
    assert '"templates"' in text


def test_build_script_never_ships_a_real_local_config():
    """The packaging step must only ever copy the *.example.yaml
    sources -- never a bare configs\\config.yaml/bounty.yaml (which
    could be the developer's own local, possibly-filled-in file)."""

    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert 'Copy-Item -Force "configs\\config.yaml"' not in text
    assert 'Copy-Item -Force "configs\\bounty.yaml"' not in text


def test_build_script_produces_a_first_run_readme():
    text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "README_FIRST_RUN.txt" in text


def test_source_example_configs_and_templates_exist():
    assert (REPO_ROOT / "configs" / "config.example.yaml").is_file()
    assert (REPO_ROOT / "configs" / "bounty.example.yaml").is_file()
    assert (REPO_ROOT / "templates").is_dir()
    assert (REPO_ROOT / "templates" / "README.md").is_file()


def test_run_guide_documents_first_run_bootstrap():
    run_guide = (REPO_ROOT / "docs" / "RUN_GUIDE.md").read_text(encoding="utf-8")
    lowered = run_guide.lower()
    assert "bootstrap" in lowered or "first run" in lowered or "first launch" in lowered
