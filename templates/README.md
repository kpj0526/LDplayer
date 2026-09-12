# templates/

Placeholder directory for future recognizer reference assets (OCR
training data, template images for template matching, etc.).

**Nothing in this repository reads from this directory yet.**
`ldmanager.recognition.PlaceholderRecognizer` is the only recognizer
implemented in MVP-001, and it never performs real image analysis — it
always reports `UNKNOWN` with zero confidence, regardless of what (if
anything) is in this folder. It exists so `mission.example.yaml`'s
`templates_dir` has somewhere real to point at, and so the shape of a
future real implementation is visible.

Do not treat the presence of this folder as evidence that recognition
works. See `docs/REAL_CAPTURE_CHECKLIST.md` for what actually needs to
happen before any file placed here would do anything.
