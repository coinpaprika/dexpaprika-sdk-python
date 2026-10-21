"""
The per-service response cache must not grow without bound.

BaseAPI caches every successful GET under an md5 key with a TTL, but nothing
used to cap how many distinct keys it would hold at once. An application that
forwards caller-chosen values (search queries, ids) into the SDK accumulated
one entry per distinct value for the life of the process. This file proves the
cache is now bounded by entry count with least-recently-used eviction, and
that a hot entry survives while a cold, unused one is the first to go.

The session is stubbed; no request leaves the process.
"""

from dexpaprika_sdk import DexPaprikaClient


class _Response:
    """Stands in for a requests.Response that always answers with an empty,
    but valid, search payload."""

    def __init__(self):
        self.status_code = 200
        self.content = b"{}"

    def json(self):
        return {}

    def raise_for_status(self):
        pass


class RecordingSession:
    """Stands in for requests.Session. Counts calls, never hits the network."""

    def __init__(self):
        self.call_count = 0

    def request(self, method, url, params=None, json=None, headers=None):
        self.call_count += 1
        return _Response()


def _client():
    return DexPaprikaClient(session=RecordingSession())


def test_cache_size_never_exceeds_the_configured_bound():
    client = _client()
    api = client.search
    bound = api.max_cache_entries

    # Ask for more distinct queries than the bound allows.
    for i in range(bound + 50):
        client.search.search(f"q{i}")
        assert len(api._cache) <= bound

    assert len(api._cache) <= bound


def test_lru_keeps_a_hot_entry_and_drops_a_cold_one():
    client = _client()
    # A small bound makes eviction happen quickly and the order easy to reason
    # about, without depending on the library default.
    client.search = type(client.search)(client, max_cache_entries=5)
    api = client.search

    for i in range(5):
        api.search(f"q{i}")

    # q0 is the oldest entry. Re-reading it (a cache hit, no new upstream call)
    # marks it most-recently-used, so it should survive the next eviction.
    calls_before_hit = client.session.call_count
    api.search("q0")
    assert client.session.call_count == calls_before_hit, "q0 should have been a cache hit"

    q0_key = api._get_cache_key("/search", {"query": "q0"})
    q1_key = api._get_cache_key("/search", {"query": "q1"})
    assert q0_key in api._cache
    assert q1_key in api._cache  # not evicted yet; bound is 5, cache holds 5

    # Push past the bound. q1 is now the least-recently-used entry (q0 was
    # refreshed, q2-q4 are newer), so it must be the one evicted.
    api.search("q5")

    assert q0_key in api._cache, "the hot entry (q0) was evicted; LRU is not working"
    assert q1_key not in api._cache, "the cold entry (q1) should have been evicted first"
    assert len(api._cache) <= 5
