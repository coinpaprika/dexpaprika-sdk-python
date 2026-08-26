"""The SDK must survive a 429, and must wait as long as the server asked.

Written after the nightly live run failed 6/31 on 2026-08-26, every failure a
429. Two separate defects sat behind that: the suite paced itself for a limit
that does not exist, and the client treated 429 as a permanent error and raised
on the first one.

The pacing is a test-suite concern. This file covers the client, which is the
half that affects every user of the SDK.
"""
import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dexpaprika_sdk import DexPaprikaClient


def _http_error(status, headers=None, body=None):
    """An HTTPError shaped like the one requests raises via raise_for_status."""
    response = MagicMock()
    response.status_code = status
    response.headers = headers or {}
    if body is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = body
    return HTTPError(f"{status} error", response=response)


class TestShouldRetry:
    def test_429_is_retryable(self):
        """The regression. A 429 is transient by definition and the API says so."""
        assert DexPaprikaClient()._should_retry(_http_error(429)) is True

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
    def test_other_4xx_are_not_retryable(self, status):
        """Retrying a deterministic 4xx only burns the caller's quota."""
        assert DexPaprikaClient()._should_retry(_http_error(status)) is False

    @pytest.mark.parametrize("status", [500, 502, 503])
    def test_5xx_still_retryable(self, status):
        assert DexPaprikaClient()._should_retry(_http_error(status)) is True


class TestRetryAfter:
    def test_reads_the_header(self):
        """api.dexpaprika.com sends `retry-after: 12` on a keyless 429."""
        e = _http_error(429, headers={"Retry-After": "12"})
        assert DexPaprikaClient()._retry_after_seconds(e) == 12.0

    def test_falls_back_to_the_body_field(self):
        """The body mirrors it as retry_after, which survives header-stripping proxies."""
        e = _http_error(429, body={"error": "rate_limited", "retry_after": 9})
        assert DexPaprikaClient()._retry_after_seconds(e) == 9.0

    def test_header_wins_over_body(self):
        e = _http_error(429, headers={"Retry-After": "3"}, body={"retry_after": 30})
        assert DexPaprikaClient()._retry_after_seconds(e) == 3.0

    def test_absent_means_none_so_the_caller_uses_normal_backoff(self):
        assert DexPaprikaClient()._retry_after_seconds(_http_error(429)) is None

    def test_http_date_is_not_guessed_at(self):
        """Retry-After may be a date. We do not parse it; None means fall back."""
        e = _http_error(429, headers={"Retry-After": "Wed, 26 Aug 2026 07:30:00 GMT"})
        assert DexPaprikaClient()._retry_after_seconds(e) is None

    def test_absurd_value_is_clamped(self):
        """A buggy or hostile value must not park a caller for an hour."""
        e = _http_error(429, headers={"Retry-After": "86400"})
        assert DexPaprikaClient()._retry_after_seconds(e) == 60.0

    def test_negative_is_floored(self):
        e = _http_error(429, headers={"Retry-After": "-5"})
        assert DexPaprikaClient()._retry_after_seconds(e) == 0.0


class TestEndToEnd:
    def test_a_429_then_a_200_recovers(self):
        """Drive the real _request path: first call 429s, second succeeds."""
        client = DexPaprikaClient()

        limited = MagicMock()
        limited.status_code = 429
        limited.headers = {"Retry-After": "0"}
        limited.content = b'{"error":"rate_limited"}'
        limited.json.return_value = {"error": "rate_limited", "retry_after": 0}
        limited.raise_for_status.side_effect = _http_error(
            429, headers={"Retry-After": "0"}
        )

        ok = MagicMock()
        ok.status_code = 200
        ok.headers = {}
        ok.content = b'[{"id":"ethereum"}]'
        ok.json.return_value = [{"id": "ethereum"}]
        ok.raise_for_status.return_value = None

        with patch.object(client.session, "request", side_effect=[limited, ok]) as m:
            result = client.get("/networks")

        assert result == [{"id": "ethereum"}]
        assert m.call_count == 2, "the 429 was not retried"

    def test_it_waits_as_long_as_the_server_asked(self):
        """The old backoff topped out at 5s, useless against a per-minute bucket."""
        client = DexPaprikaClient()

        limited = MagicMock()
        limited.status_code = 429
        limited.headers = {"Retry-After": "12"}
        limited.content = b"{}"
        limited.json.return_value = {"retry_after": 12}
        limited.raise_for_status.side_effect = _http_error(
            429, headers={"Retry-After": "12"}
        )

        ok = MagicMock()
        ok.status_code = 200
        ok.headers = {}
        ok.content = b"[]"
        ok.json.return_value = []
        ok.raise_for_status.return_value = None

        slept = []
        with patch.object(client.session, "request", side_effect=[limited, ok]), \
             patch("dexpaprika_sdk.client.time.sleep", side_effect=slept.append):
            client.get("/networks")

        assert slept, "nothing slept between the 429 and the retry"
        # Jitter is +/-10%, so 12s lands in [10.8, 13.2]. The point is that it is
        # nowhere near the old 0.1s first backoff step.
        assert 10.0 <= slept[0] <= 14.0, f"waited {slept[0]}s, expected about 12s"

    def test_a_404_still_fails_immediately(self):
        """Guard against making every 4xx retryable by accident."""
        client = DexPaprikaClient()

        missing = MagicMock()
        missing.status_code = 404
        missing.headers = {}
        missing.content = b"{}"
        missing.json.return_value = {}
        missing.raise_for_status.side_effect = _http_error(404)

        with patch.object(client.session, "request", return_value=missing) as m:
            with pytest.raises(Exception):
                client.get("/networks")

        assert m.call_count == 1, "a 404 should not be retried"
