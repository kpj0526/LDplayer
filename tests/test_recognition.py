from pathlib import Path

from ldmanager.coordinates import RelativeRegion
from ldmanager.recognition import PlaceholderRecognizer, RecognitionStatus


def test_placeholder_recognizer_never_matches():
    recognizer = PlaceholderRecognizer()
    roi = RelativeRegion(x=0.0, y=0.0, width=0.1, height=0.1)

    result = recognizer.recognize(b"\x89PNG\r\n\x1a\n", roi, "ANY_LABEL", 0.9)

    assert result.matched is False
    assert result.status is RecognitionStatus.UNKNOWN
    assert result.confidence == 0.0
    assert result.label is None


def test_placeholder_recognizer_never_matches_regardless_of_input():
    recognizer = PlaceholderRecognizer(templates_dir=Path("templates"))
    roi = RelativeRegion(x=0.2, y=0.2, width=0.3, height=0.3)

    # Even garbage/empty bytes and a low threshold must not produce a match.
    result = recognizer.recognize(b"", roi, "200/200", 0.0)

    assert result.matched is False


def test_placeholder_recognizer_stores_templates_dir_but_does_not_read_it(tmp_path):
    missing_dir = tmp_path / "does_not_exist"
    recognizer = PlaceholderRecognizer(templates_dir=missing_dir)
    roi = RelativeRegion(x=0.0, y=0.0, width=0.1, height=0.1)

    # Must not raise even though templates_dir doesn't exist on disk --
    # it is never read by the placeholder.
    result = recognizer.recognize(b"data", roi, "X", 0.5)
    assert result.matched is False
    assert recognizer.templates_dir == missing_dir
