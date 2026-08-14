"""Optional API key, and the header rules that go with it.

Keyless is the default and must keep working untouched. The Bearer rule is the
regression this file exists for: `Authorization: Bearer api_...` returns 401
because the API checksums the raw header value, and the mistake has resurfaced
three times in four months.
"""
import pytest

from dexpaprika_sdk import DexPaprikaClient
from dexpaprika_sdk.client import _resolve_api_key


class RecordingSession:
    """Stands in for requests.Session and remembers the headers it was given."""

    def __init__(self, status_code=200, payload=None):
        self.calls = []
        self._status_code = status_code
        self._payload = payload if payload is not None else []

    def request(self, method, url, params=None, json=None, headers=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}})
        return _Response(self._status_code, self._payload)


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.content = b"[]"

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError("unexpected error status in this fixture")


def headers_for(**kwargs):
    session = RecordingSession()
    client = DexPaprikaClient(session=session, **kwargs)
    client.get("/networks")
    return session.calls[0]["headers"]


# ── The Bearer rule ────────────────────────────────────────────────────────

def test_key_is_the_entire_authorization_value():
    assert headers_for(api_key="api_abc123")["Authorization"] == "api_abc123"


@pytest.mark.parametrize("scheme", ["Bearer", "Token", "ApiKey", "Basic", "Key"])
def test_no_scheme_word_is_ever_prepended(scheme):
    value = headers_for(api_key="api_abc123")["Authorization"]
    assert not value.lower().startswith(scheme.lower())


# ── Keyless stays the default ──────────────────────────────────────────────

def test_no_key_sends_no_authorization_header(monkeypatch):
    monkeypatch.delenv("DEXPAPRIKA_API_KEY", raising=False)
    assert "Authorization" not in headers_for()


@pytest.mark.parametrize("value", ["", "   ", "\t"])
def test_blank_key_is_keyless_not_an_empty_header(monkeypatch, value):
    monkeypatch.delenv("DEXPAPRIKA_API_KEY", raising=False)
    assert "Authorization" not in headers_for(api_key=value)


# ── Precedence ─────────────────────────────────────────────────────────────

def test_environment_variable_is_used_when_no_argument_is_given(monkeypatch):
    monkeypatch.setenv("DEXPAPRIKA_API_KEY", "api_from_env")
    assert headers_for()["Authorization"] == "api_from_env"


def test_explicit_argument_beats_the_environment(monkeypatch):
    monkeypatch.setenv("DEXPAPRIKA_API_KEY", "api_from_env")
    assert headers_for(api_key="api_explicit")["Authorization"] == "api_explicit"


def test_surrounding_whitespace_is_trimmed(monkeypatch):
    monkeypatch.setenv("DEXPAPRIKA_API_KEY", "  api_padded\n")
    assert _resolve_api_key(None) == "api_padded"


# ── Header injection ───────────────────────────────────────────────────────

@pytest.mark.parametrize("value", ["api_a\r\nX-Evil: 1", "api_a\nb", "api_a\0b"])
def test_a_key_with_control_characters_is_dropped(value):
    assert _resolve_api_key(value) is None


# ── Identification ─────────────────────────────────────────────────────────

def test_user_agent_reports_the_real_package_version():
    from dexpaprika_sdk import __version__
    assert headers_for()["User-Agent"] == f"DexPaprika-SDK-Python/{__version__}"


def test_user_agent_is_not_the_literal_that_went_stale():
    # Pinned to 0.5.1 while the package shipped 0.8.0, so every request lied
    # about which SDK sent it.
    assert headers_for()["User-Agent"] != "DexPaprika-SDK-Python/0.5.1"


def test_a_caller_supplied_user_agent_still_wins():
    assert headers_for(user_agent="my-app/1.0")["User-Agent"] == "my-app/1.0"


# ── Host rules ─────────────────────────────────────────────────────────────

def test_a_key_alone_never_changes_the_host(monkeypatch):
    # Free keys are served from the default host; only Pro moves to api-pro, and
    # sending a free key there returns 403. Guessing would break the people who
    # just registered.
    monkeypatch.delenv("DEXPAPRIKA_API_KEY", raising=False)
    session = RecordingSession()
    DexPaprikaClient(session=session, api_key="api_abc123").get("/networks")
    # Exact rather than a prefix: a startswith check on a URL is the shape of a
    # broken host allowlist, and CodeQL is right to flag it even in a test.
    assert session.calls[0]["url"] == "https://api.dexpaprika.com/networks"


def test_pro_customers_set_the_host_explicitly():
    session = RecordingSession()
    DexPaprikaClient(
        session=session, api_key="api_abc123", base_url="https://api-pro.dexpaprika.com"
    ).get("/networks")
    assert session.calls[0]["url"] == "https://api-pro.dexpaprika.com/networks"
