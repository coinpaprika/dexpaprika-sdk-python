#!/usr/bin/env python3
"""Live tests for the advanced pool search (/frontend/v1) endpoint.

These hit the real API, in the same style as test_all_endpoints.py. They cover
the global and per-network variants, cursor pagination, the canonical->wire sort
translation (sort_by/sort_dir -> order_by/sort), filters, and the detailed token
metadata + per-timeframe metric blocks.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dexpaprika_sdk import DexPaprikaClient


@pytest.fixture
def client():
    return DexPaprikaClient()


@pytest.fixture
def test_data():
    return {
        "ethereum_network": "ethereum",
        "test_dex": "uniswap_v3",
    }


def test_advanced_search_global(client):
    """Global search returns a non-empty, cursor-paginated result set."""
    resp = client.pools.advanced_search(limit=5)
    assert resp is not None
    assert hasattr(resp, "results")
    assert hasattr(resp, "has_next_page")
    assert hasattr(resp, "next_cursor")
    assert hasattr(resp, "query")
    assert len(resp.results) > 0
    row = resp.results[0]
    assert row.id
    assert hasattr(row, "volume_usd_24h")
    assert hasattr(row, "tokens")


def test_advanced_search_by_network(client, test_data):
    """Per-network search hits /frontend/v1/networks/{network}/pools."""
    resp = client.pools.advanced_search(
        network=test_data["ethereum_network"], limit=5
    )
    assert resp is not None
    assert len(resp.results) > 0
    # The query echo reports the network the backend applied.
    assert resp.query.get("network") == test_data["ethereum_network"]
    for row in resp.results:
        assert row.chain == test_data["ethereum_network"]


def test_advanced_search_sort_translation(client, test_data):
    """Canonical sort_by/sort_dir must be sent on the wire as order_by/sort."""
    resp = client.pools.advanced_search(
        network=test_data["ethereum_network"],
        sort_by="volume_usd_24h",
        sort_dir="desc",
        limit=10,
    )
    assert resp is not None
    # The wire param names show up in the echoed query, proving translation.
    assert resp.query.get("order_by") == "volume_usd_24h"
    assert resp.query.get("sort") == "desc"
    assert "sort_by" not in resp.query
    assert "sort_dir" not in resp.query
    # And the results actually come back sorted descending by 24h volume.
    volumes = [r.volume_usd_24h for r in resp.results if r.volume_usd_24h is not None]
    assert volumes == sorted(volumes, reverse=True)


def test_advanced_search_filter_works(client, test_data):
    """A price + dex filter narrows the result set to matching pools."""
    resp = client.pools.advanced_search(
        network=test_data["ethereum_network"],
        price_usd_min=0.5,
        dex_name=test_data["test_dex"],
        limit=10,
    )
    assert resp is not None
    assert len(resp.results) > 0
    for row in resp.results:
        assert row.dex_id == test_data["test_dex"]
        if row.price_usd is not None:
            assert row.price_usd >= 0.5


def test_advanced_search_cursor_pagination(client):
    """next_cursor advances the window to a different second page.

    We don't require fully disjoint pages: this is a live, high-volume feed and
    rankings shift slightly between calls, so a pool sitting on the page boundary
    can surface in both. What we assert is that the cursor genuinely moves the
    window forward, i.e. the two pages are not identical.
    """
    first = client.pools.advanced_search(limit=3)
    assert first.has_next_page is True
    assert first.next_cursor
    second = client.pools.advanced_search(limit=3, cursor=first.next_cursor)
    assert second is not None
    assert len(second.results) > 0
    first_ids = [r.id for r in first.results]
    second_ids = [r.id for r in second.results]
    assert first_ids != second_ids
    # The second page should surface at least one pool the first did not.
    assert set(second_ids) - set(first_ids)


def test_advanced_search_detailed_tokens(client, test_data):
    """detailed=True enriches tokens with metadata and timeframe metric blocks."""
    resp = client.pools.advanced_search(
        network=test_data["ethereum_network"],
        detailed=True,
        limit=5,
    )
    assert resp is not None
    assert len(resp.results) > 0
    # Find a token that came back enriched (the API may omit some fields, so we
    # look across rows rather than hard-requiring any single token).
    enriched = [
        t
        for row in resp.results
        for t in row.tokens
        if t.symbol is not None
    ]
    assert enriched, "expected at least one detailed token with a symbol"
    token = enriched[0]
    assert token.id
    assert token.decimals is not None
    # At least one timeframe metric block should be populated.
    blocks = [
        t.hour24
        for row in resp.results
        for t in row.tokens
        if t.hour24 is not None
    ]
    assert blocks, "expected at least one 24h timeframe metric block"


def test_advanced_search_basic_tokens_minimal(client, test_data):
    """Without detailed, tokens carry only the minimal id/chain shape."""
    resp = client.pools.advanced_search(
        network=test_data["ethereum_network"], limit=3
    )
    assert resp is not None
    assert len(resp.results) > 0
    token = resp.results[0].tokens[0]
    assert token.id
    # Basic mode does not populate symbol; this must not raise.
    assert token.symbol is None


def test_advanced_search_invalid_sort_by(client):
    """An unknown sort_by is rejected before any request is made."""
    with pytest.raises(ValueError):
        client.pools.advanced_search(sort_by="not_a_field")


def test_advanced_search_alias_method(client):
    """pools.search is an alias for pools.advanced_search."""
    assert client.pools.search == client.pools.advanced_search
    resp = client.pools.search(limit=2)
    assert resp is not None
    assert len(resp.results) > 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
