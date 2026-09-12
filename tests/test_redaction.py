from ldmanager.redaction import REDACTED_PLACEHOLDER, redact_sensitive_text


def test_redacts_password_kv():
    result = redact_sensitive_text("login attempt password=hunter2secret")
    assert "hunter2secret" not in result
    assert REDACTED_PLACEHOLDER in result


def test_redacts_token_colon_form():
    result = redact_sensitive_text("token: abc123")
    assert "abc123" not in result
    assert REDACTED_PLACEHOLDER in result


def test_redacts_api_key_variants():
    for text in ("api_key=sk-live-1", "api-key: sk-live-1", "apikey=sk-live-1"):
        assert "sk-live-1" not in redact_sensitive_text(text)


def test_redacts_authorization_bearer_full_token():
    result = redact_sensitive_text("Authorization: Bearer eyJhbGciOi.abc.def")
    assert "eyJhbGciOi" not in result
    assert REDACTED_PLACEHOLDER in result


def test_redacts_cookie_header_full_value():
    result = redact_sensitive_text("Cookie: session=abc123; other=1")
    assert "abc123" not in result
    assert REDACTED_PLACEHOLDER in result


def test_redacts_credential_and_secret_and_private_key():
    assert "xval" not in redact_sensitive_text("credential=xval")
    assert "xval" not in redact_sensitive_text("secret: xval")
    assert "xval" not in redact_sensitive_text("private_key=xval")


def test_leaves_non_sensitive_text_untouched():
    text = "account LD1 state=online adb_serial=127.0.0.1:5555"
    assert redact_sensitive_text(text) == text


def test_empty_string_returns_empty():
    assert redact_sensitive_text("") == ""


def test_quoted_value_is_fully_redacted():
    result = redact_sensitive_text('password="hunter 2 with spaces"')
    assert "hunter" not in result
    assert REDACTED_PLACEHOLDER in result
