"""
Typed exceptions for the DexPaprika SDK.

The API self-documents deprecations: when an endpoint is removed or deprecated
it returns a non-2xx response whose JSON body carries a "replacement" field
pointing at the endpoint to use instead, for example::

    {"code": 410, "message": "endpoint removed",
     "replacement": "/networks/{network}/pools/search"}

The client turns any such response into a ``DeprecatedEndpointError`` so that
callers (and their logs) see both the API's own message and the replacement
without having to inspect the raw response body.
"""

from requests.exceptions import HTTPError


class DexPaprikaError(Exception):
    """Base class for all typed errors raised by the DexPaprika SDK."""


class DeprecatedEndpointError(DexPaprikaError):
    """Raised when an error response carries a "replacement" deprecation hint.

    This is generic: it fires for any error status whose body contains a
    "replacement" field, not just HTTP 410, so future deprecations surface
    the same way without SDK changes.

    Attributes:
        replacement: The endpoint path the API tells you to use instead.
        api_message: The raw "message" value from the response body.
        status_code: The HTTP status code of the error response, if known.
        response: The underlying ``requests.Response``, if available.
    """

    def __init__(self, message, replacement, status_code=None, response=None):
        self.api_message = message
        self.replacement = replacement
        self.status_code = status_code
        self.response = response

        full_message = message or "endpoint removed"
        if replacement:
            full_message = f"{full_message}. Use {replacement} instead."
        super().__init__(full_message)


class ApiHTTPError(HTTPError):
    """HTTPError carrying the API's own error fields, when the body has them.

    Some error bodies include ``error`` (a machine-readable code, e.g.
    "plan_required"), ``required_tier`` (the plan that lifts the restriction)
    and ``param`` (the request parameter that triggered it), for example the
    403 a keyless caller gets for paging a search endpoint past the first
    page::

        {"error": "plan_required", "tier": "keyless", "required_tier": "free",
         "param": "cursor", "message": "..."}

    Any error response without these fields (a plain 400 or 404 with just a
    "message") raises this with all three set to None, so callers never have
    to special-case which errors carry them.

    Still a ``requests.exceptions.HTTPError``, so existing
    ``except requests.exceptions.HTTPError:`` handlers keep working unchanged.

    Attributes:
        error_code: The body's "error" field (named to avoid shadowing the
            builtin), or None.
        required_tier: The body's "required_tier" field, or None.
        param: The body's "param" field, or None.
    """

    def __init__(self, message, response=None, error_code=None, required_tier=None, param=None):
        self.error_code = error_code
        self.required_tier = required_tier
        self.param = param
        super().__init__(message, response=response)
