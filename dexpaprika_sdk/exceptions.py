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
