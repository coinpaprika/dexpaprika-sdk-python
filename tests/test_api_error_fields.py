"""error/required_tier/param on the raised exception.

The search endpoints (/pools/search, /tokens/search and their network-scoped
variants) will start returning a 403 whose body names the plan that lifts the
restriction, e.g. paging a search endpoint without an API key:

    {"error": "plan_required", "tier": "keyless", "required_tier": "free",
     "param": "cursor", "message": "..."}

The client exposes those three fields as attributes on the raised exception
(ApiHTTPError), which remains a requests.exceptions.HTTPError so existing
`except requests.exceptions.HTTPError:` callers keep working unchanged. Any
error body without those fields (a plain 400 or 404 with just "message")
raises the same type with all three set to None.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dexpaprika_sdk import DexPaprikaClient
from dexpaprika_sdk.exceptions import ApiHTTPError


def _response(status, body):
    response = MagicMock()
    response.status_code = status
    response.url = "https://api.dexpaprika.com/networks/ethereum/pools/search"
    response.content = b"body"
    response.json.return_value = body
    response.raise_for_status.side_effect = HTTPError(f"{status} error", response=response)
    return response


def test_plan_required_403_exposes_error_fields():
    """The exact body a keyless caller gets for paging a search endpoint."""
    body = {
        "error": "plan_required",
        "tier": "keyless",
        "required_tier": "free",
        "param": "cursor",
        "message": (
            "Search results beyond the first page require an API key (free "
            "key: all pages). Create one in under a minute at "
            "https://console.dexpaprika.com"
        ),
        "links": {
            "register": "https://console.dexpaprika.com",
            "pricing": "https://dexpaprika.com/api/pricing",
            "docs": "https://docs.dexpaprika.com/knowledge-base/rate-limits#pagination-rules",
            "coupon": "https://dexpaprika.com/api/pricing?coupon=START10",
        },
    }
    client = DexPaprikaClient()

    with patch.object(client.session, "request", return_value=_response(403, body)):
        with pytest.raises(ApiHTTPError) as excinfo:
            client.get("/networks/ethereum/pools/search")

    err = excinfo.value
    assert isinstance(err, HTTPError)
    assert err.error_code == "plan_required"
    assert err.required_tier == "free"
    assert err.param == "cursor"


def test_generic_404_leaves_fields_none():
    """An error body with just 'message' must not crash, and names nothing."""
    body = {"message": "pool not found"}
    client = DexPaprikaClient()

    with patch.object(client.session, "request", return_value=_response(404, body)):
        with pytest.raises(ApiHTTPError) as excinfo:
            client.get("/networks/ethereum/pools/0xdoesnotexist")

    err = excinfo.value
    assert isinstance(err, HTTPError)
    assert err.error_code is None
    assert err.required_tier is None
    assert err.param is None


def test_raised_exception_is_still_an_http_error_for_existing_callers():
    """Existing `except requests.exceptions.HTTPError:` handlers must keep working."""
    body = {"error": "plan_required", "required_tier": "free", "param": "cursor", "message": "no paging"}
    client = DexPaprikaClient()

    with patch.object(client.session, "request", return_value=_response(403, body)):
        try:
            client.get("/pools/search")
            assert False, "expected an HTTPError"
        except HTTPError as e:
            assert e.error_code == "plan_required"
