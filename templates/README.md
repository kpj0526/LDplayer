# templates/

Template-matching reference assets read by
`ldmanager.recognition.OpenCVTemplateRecognizer` via
`configs/bounty.example.yaml`'s `template_map` (and your own,
git-ignored `configs/bounty.yaml`, which should point at the same
`templates_dir`). `ldmanager.recognition.PlaceholderRecognizer` (the
safe fallback when OpenCV/numpy aren't installed) still never reads
this folder — it always reports `UNKNOWN`.

Most files here remain uncalibrated placeholders/legacy crops — see
`docs/REAL_CAPTURE_CHECKLIST.md` for what real calibration requires.
The `mission_header.png`, `mission_objective_label.png`,
`complete_badge.png`, `currency_action_4400.png`, and
`mission_target_phrase.png` files are the exception: they are real
crops of real, customer-supplied 1280x720 captures (GAME-CAL-001's
"REAL-CAPTURE REWORK"), with documented provenance and a passing real-
asset regression test — see `tests/fixtures/game_cal_001/PROVENANCE.md`
and `tests/test_screen_classification_real_assets.py`.

Do not treat the mere presence of a file here as evidence recognition
works against your own game version/resolution — always verify with
your own real captures before relying on any of these.
