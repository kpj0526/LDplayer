import pytest

from ldmanager.paths import UnsafePathError, ensure_safe_subdir, sanitize_filename


def test_sanitize_filename_strips_unsafe_chars():
    assert sanitize_filename("my file!.png") == "my_file_.png"


def test_sanitize_filename_drops_directory_components():
    assert sanitize_filename("../../etc/passwd") == "passwd"


def test_sanitize_filename_falls_back_for_dot_segments():
    assert sanitize_filename("..") == "file"
    assert sanitize_filename(".") == "file"
    assert sanitize_filename("") == "file"


def test_sanitize_filename_custom_default():
    assert sanitize_filename("", default="untitled") == "untitled"


def test_ensure_safe_subdir_builds_expected_path(tmp_path):
    result = ensure_safe_subdir(tmp_path, "LD1")
    assert result == tmp_path / "LD1"


def test_ensure_safe_subdir_supports_multiple_segments(tmp_path):
    result = ensure_safe_subdir(tmp_path, "LD1", "sub")
    assert result == tmp_path / "LD1" / "sub"


def test_ensure_safe_subdir_rejects_traversal_segment(tmp_path):
    with pytest.raises(UnsafePathError):
        ensure_safe_subdir(tmp_path, "..")


def test_ensure_safe_subdir_rejects_separator_in_segment(tmp_path):
    with pytest.raises(UnsafePathError):
        ensure_safe_subdir(tmp_path, "a/b")


def test_ensure_safe_subdir_rejects_empty_segment(tmp_path):
    with pytest.raises(UnsafePathError):
        ensure_safe_subdir(tmp_path, "")
