#!/usr/bin/env python3

import sys
import os
import time
import pytest
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dexpaprika_sdk import DexPaprikaClient

# Create a fixture for the client to be reused across tests
@pytest.fixture
def client():
    return DexPaprikaClient()

# Create a fixture for test data
@pytest.fixture
def test_data():
    return {
        "ethereum_network": "ethereum",
        "test_pool_network": "ethereum",
        "test_pool_address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",  # USDC/WETH on Uniswap v3
        "test_dex": "uniswap_v3",  # Uniswap V3 on Ethereum
        "test_token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC on Ethereum
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d"),
    }

# Networks API tests
def test_networks_list(client):
    networks = client.networks.list()
    assert networks is not None
    assert len(networks) > 0

def test_networks_list_dexes(client, test_data):
    dexes = client.networks.list_dexes(test_data["ethereum_network"])
    assert dexes is not None
    assert hasattr(dexes, 'dexes')

# Utils API tests
def test_utils_get_stats(client):
    stats = client.utils.get_stats()
    assert stats is not None
    assert hasattr(stats, 'chains')
    assert hasattr(stats, 'pools')
    assert hasattr(stats, 'tokens')

# Pools API tests
def test_pools_list_deprecated(client):
    """Test the deprecated global pools method with deprecation warning."""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pools_response = client.pools.list(limit=5)
        assert pools_response is not None
        # The unified search response exposes rows under `results`
        assert hasattr(pools_response, 'results')
        assert hasattr(pools_response, 'has_next_page')
        assert len(pools_response.results) > 0
        # `pools` remains as a backward-compatible alias for `results`
        assert pools_response.pools == pools_response.results
        # Check that a deprecation warning was issued
        assert len(w) > 0
        assert any("deprecated" in str(warning.message).lower() for warning in w)

def test_pools_list_by_network_primary(client, test_data):
    """Test the primary pools list method using network-specific endpoint."""
    pools_response = client.pools.list_by_network(test_data["ethereum_network"], limit=5)
    assert pools_response is not None
    assert hasattr(pools_response, 'results')
    assert len(pools_response.results) > 0
    # New search item shape: pool address under `id`, timeframe-split volume
    pool = pools_response.results[0]
    assert hasattr(pool, 'id')
    assert hasattr(pool, 'volume_usd_24h')
    assert hasattr(pool, 'transactions_24h')

def test_dexes_list(client, test_data):
    dexes_response = client.dexes.list(test_data["ethereum_network"])
    assert dexes_response is not None
    assert hasattr(dexes_response, 'dexes')

def test_pools_list_by_dex_is_gone(client, test_data):
    """The per-DEX pool listing was removed from the API and answers 410.

    This test used to assert a successful response. It started failing on main
    with no code change on our side, once /networks/{network}/dexes/{dex}/pools
    began returning 410. The SDK behaviour is right: it raises
    DeprecatedEndpointError and carries the replacement path through, so a
    caller finds out where to go instead of getting an opaque HTTP error. What
    was stale was the expectation.
    """
    from dexpaprika_sdk.exceptions import DeprecatedEndpointError

    with pytest.raises(DeprecatedEndpointError) as excinfo:
        client.pools.list_by_dex(
            test_data["ethereum_network"],
            test_data["test_dex"],
            limit=5
        )

    # The replacement is the useful part of this exception, so pin it rather
    # than just the type.
    assert "pools/search" in excinfo.value.replacement

def test_pools_get_details(client, test_data):
    pool_details = client.pools.get_details(
        test_data["test_pool_network"], 
        test_data["test_pool_address"]
    )
    assert pool_details is not None
    assert hasattr(pool_details, 'tokens')

def test_pools_get_ohlcv(client, test_data):
    ohlcv = client.pools.get_ohlcv(
        test_data["test_pool_network"],
        test_data["test_pool_address"],
        start=test_data["start_date"],
        end=test_data["end_date"],
        limit=5,
        interval="24h"
    )
    assert ohlcv is not None

def test_pools_get_transactions(client, test_data):
    transactions = client.pools.get_transactions(
        test_data["test_pool_network"], 
        test_data["test_pool_address"], 
        limit=5
    )
    assert transactions is not None
    assert hasattr(transactions, 'transactions')

# Tokens API tests
def test_tokens_get_details(client, test_data):
    token_details = client.tokens.get_details(
        test_data["test_pool_network"], 
        test_data["test_token_address"]
    )
    assert token_details is not None
    assert hasattr(token_details, 'name')
    assert hasattr(token_details, 'symbol')

def test_tokens_get_pools(client, test_data):
    """tokens.get_pools targets /pools/search with token_address: every
    returned pool must contain the requested token and pagination is
    cursor-based."""
    token_pools = client.tokens.get_pools(
        test_data["test_pool_network"],
        test_data["test_token_address"],
        limit=5
    )
    assert token_pools is not None
    assert hasattr(token_pools, 'results')
    assert len(token_pools.pools) > 0  # backward-compatible alias for results
    for pool in token_pools.pools:
        token_ids = [t.id for t in pool.tokens]
        assert test_data["test_token_address"] in token_ids

    # Follow the cursor to the next page
    if token_pools.has_next_page and token_pools.next_cursor:
        next_page = client.tokens.get_pools(
            test_data["test_pool_network"],
            test_data["test_token_address"],
            limit=5,
            cursor=token_pools.next_cursor
        )
        assert next_page is not None
        assert len(next_page.results) > 0
        assert next_page.results[0].id != token_pools.results[0].id

def test_tokens_get_pools_deprecated_params(client, test_data):
    """The removed endpoint's pair filter (address) and reorder options have
    no /pools/search equivalent: they must warn and be ignored, not sent."""
    import warnings
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        token_pools = client.tokens.get_pools(
            test_data["test_pool_network"],
            test_data["test_token_address"],
            limit=5,
            address="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            reorder=True
        )
        assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert token_pools is not None
    # The call still succeeds and still filters by the primary token
    for pool in token_pools.pools:
        token_ids = [t.id for t in pool.tokens]
        assert test_data["test_token_address"] in token_ids

# Pool Filter API tests
def test_pools_filter(client, test_data):
    """Test pool filtering with volume constraint."""
    filtered = client.pools.filter(
        test_data["ethereum_network"],
        volume_24h_min=100000,
        limit=5
    )
    assert filtered is not None
    assert hasattr(filtered, 'results')
    # Cursor-based pagination: has_next_page / next_cursor, not page_info
    assert hasattr(filtered, 'has_next_page')
    assert hasattr(filtered, 'next_cursor')
    assert len(filtered.results) > 0
    # Verify each pool has the expected fields
    pool = filtered.results[0]
    assert hasattr(pool, 'id')
    # The search endpoint returns timeframe-split volume, not a flat volume_usd
    assert hasattr(pool, 'volume_usd_24h')
    assert hasattr(pool, 'tokens')

def test_pools_filter_multiple_params(client, test_data):
    """Test pool filtering with multiple constraints."""
    filtered = client.pools.filter(
        test_data["ethereum_network"],
        volume_24h_min=50000,
        txns_24h_min=10,
        sort_by="volume_24h",
        sort_dir="desc",
        limit=3
    )
    assert filtered is not None
    assert hasattr(filtered, 'results')

# Price-change window tests
#
# The search endpoint echoes the parameters it recognised under `query`. That
# echo is the only reliable proof these reached the wire: the SDK maps an
# unknown sort field to volume_usd_24h before sending, and the API ignores an
# unknown filter name and still answers 200 with a full result set. Both
# failures look like a successful call returning the wrong pools.
#
# The three short windows below are the pool-only ones. The 24h window is not:
# /tokens/search sorts and filters on it too.

PRICE_CHANGE_WINDOWS = [
    "price_change_percentage_6h",
    "price_change_percentage_1h",
    "price_change_percentage_5m",
]


def _measured_bound(client, network, field, sort_dir, rank=10):
    """Read a live threshold off the endpoint instead of hardcoding one.

    A fixed bound like 50% passes vacuously on a quiet hour: every row of an
    empty result set satisfies the loop that checks it. So sort by the field,
    take the value sitting at ``rank``, and halve it. At least ``rank`` pools
    are then above the bound with room to spare, which turns an empty filtered
    set back into a real failure.

    Returns the bound and the ranked values it came from.
    """
    ranked = client.pools.list_by_network(
        network, order_by=field, sort=sort_dir, limit=rank * 2
    )
    values = [
        getattr(pool, field) for pool in ranked.results
        if getattr(pool, field) is not None
    ]
    assert len(values) >= rank, f"only {len(values)} pools carry {field}"
    return round(values[rank - 1] / 2, 4), values

def test_pools_sort_by_price_change_windows(client, test_data):
    """Each new pool sort window must survive the canonical mapping, and the
    row must expose the value it was sorted on."""
    for window in PRICE_CHANGE_WINDOWS:
        pools = client.pools.list_by_network(
            test_data["ethereum_network"], order_by=window, limit=5
        )
        assert pools.query is not None
        # Not volume_usd_24h: that is what a missing canonical entry produces.
        assert pools.query.get("order_by") == window, window
        assert len(pools.results) > 0
        assert getattr(pools.results[0], window) is not None, window

def test_pools_filter_price_change_window(client, test_data):
    """A price-change bound must narrow the result set, not just return 200."""
    bound, ranked = _measured_bound(
        client, test_data["ethereum_network"], "price_change_percentage_1h", "desc"
    )
    assert bound > 0, f"no 1h movers on ethereum right now: {ranked[:3]}"

    filtered = client.pools.filter(
        test_data["ethereum_network"],
        price_change_percentage_1h_min=bound,
        limit=10
    )
    assert filtered.query is not None
    assert filtered.query.get("price_change_percentage_1h_min") == pytest.approx(bound)
    # Ten pools were above this a moment ago, so an empty page is the bound
    # failing, not a quiet market.
    assert len(filtered.results) > 0, f"bound {bound} matched nothing"
    for pool in filtered.results:
        assert pool.price_change_percentage_1h is not None, pool.id
        assert pool.price_change_percentage_1h >= bound

    # Contrast against an unfiltered baseline. Top pools by volume sit near zero
    # on the hour, so without the bound the same query serves rows below it.
    baseline = client.pools.list_by_network(test_data["ethereum_network"], limit=10)
    assert any(
        p.price_change_percentage_1h is not None and p.price_change_percentage_1h < bound
        for p in baseline.results
    )

def test_pools_filter_negative_price_change(client, test_data):
    """Negative bounds are the point: a negative max selects pools that fell.

    The threshold is measured off the ascending sort for the same reason as the
    positive case, so the test does not depend on how bad a given day is.
    """
    bound, ranked = _measured_bound(
        client, test_data["ethereum_network"], "price_change_percentage_24h", "asc"
    )
    assert bound < 0, f"nothing is down on ethereum right now: {ranked[:3]}"

    filtered = client.pools.filter(
        test_data["ethereum_network"],
        price_change_percentage_24h_max=bound,
        limit=10
    )
    assert filtered.query is not None
    assert filtered.query.get("price_change_percentage_24h_max") == pytest.approx(bound)
    assert len(filtered.results) > 0, f"bound {bound} matched nothing"
    for pool in filtered.results:
        assert pool.price_change_percentage_24h is not None, pool.id
        assert pool.price_change_percentage_24h <= bound

    baseline = client.pools.list_by_network(test_data["ethereum_network"], limit=10)
    assert any(
        p.price_change_percentage_24h is not None and p.price_change_percentage_24h > bound
        for p in baseline.results
    )

def test_short_price_change_windows_are_pool_only(client, test_data):
    """Pin the sort-side asymmetry so a later sweep does not add these to tokens.

    /tokens/search returns 400 for the 6h/1h/5m windows and token rows carry no
    5m field at all. The SDK keeps them out of the token sort set on purpose.
    The 24h window is not in that group: it sorts on both endpoints, so
    TOKEN_SORT_CANONICAL carries it and this test leaves it alone.
    """
    from requests.exceptions import HTTPError
    from dexpaprika_sdk.api.base import (
        POOL_SORT_CANONICAL, TOKEN_SORT_CANONICAL, map_token_sort_field,
    )

    windows = set(PRICE_CHANGE_WINDOWS)
    assert windows <= POOL_SORT_CANONICAL
    assert not (windows & TOKEN_SORT_CANONICAL)
    for window in windows:
        # Anything unknown to /tokens/search falls back to volume_usd_24h.
        assert map_token_sort_field(window) == "volume_usd_24h"

    # And the API still rejects the window on the token side.
    with pytest.raises(HTTPError):
        client.get(
            f"/networks/{test_data['ethereum_network']}/tokens/search",
            params={"order_by": "price_change_percentage_5m", "limit": 1},
        )

def test_tokens_get_top_price_change_window_falls_back(client, test_data):
    """A pool-only window passed to tokens.get_top must not reach the wire."""
    top = client.tokens.get_top(
        test_data["ethereum_network"],
        order_by="price_change_percentage_5m",
        limit=3
    )
    assert top.query is not None
    assert top.query.get("order_by") == "volume_usd_24h"
    assert len(top.results) > 0

def test_tokens_filter_price_change_24h(client, test_data):
    """The 24h bound is the one price-change filter /tokens/search applies.

    The bound is fixed rather than measured because the token side ranks by
    percentage across every token on the chain, where the top rows run to
    absurd numbers. 20% is a threshold something on ethereum always clears, and
    an empty page fails the test loudly instead of passing vacuously.
    """
    network = test_data["ethereum_network"]
    filtered = client.tokens.filter(
        network, price_change_percentage_24h_min=20, limit=6
    )
    assert filtered.query is not None
    assert filtered.query.get("price_change_percentage_24h_min") == 20
    assert len(filtered.results) > 0
    for token in filtered.results:
        assert token.price_change_percentage_24h is not None, token.address
        assert token.price_change_percentage_24h >= 20

    # Contrast: the same query without the bound is ordered by volume, and the
    # highest-volume tokens on ethereum sit near flat.
    baseline = client.tokens.filter(network, limit=6)
    assert any(
        t.price_change_percentage_24h is not None and t.price_change_percentage_24h < 20
        for t in baseline.results
    )

def test_tokens_filter_ignores_short_window_bounds(client, test_data):
    """The short bounds are not offered on tokens because the API drops them.

    tokens.filter() raises TypeError rather than sending a 6h bound. Sending one
    by hand shows why the SDK refuses: HTTP 200, and the bound missing from the
    `query` echo, which lists only what the endpoint recognised. Off the wire the
    rows come back identical to the unfiltered call. A silently ignored bound is
    worse than an error.
    """
    network = test_data["ethereum_network"]
    with pytest.raises(TypeError):
        client.tokens.filter(network, price_change_percentage_6h_min=20)

    raw = client.get(
        f"/networks/{network}/tokens/search",
        params={"limit": 6, "price_change_percentage_6h_min": 20},
    )
    assert "price_change_percentage_6h_min" not in raw.get("query", {})

# Top Tokens API tests
def test_tokens_get_top(client, test_data):
    """Test getting top tokens on a network."""
    top_tokens = client.tokens.get_top(test_data["ethereum_network"], limit=5)
    assert top_tokens is not None
    # Unified search response: rows under `results`, cursor pagination
    assert hasattr(top_tokens, 'results')
    assert hasattr(top_tokens, 'has_next_page')
    assert len(top_tokens.results) > 0
    # New flat token search item: identified by address, no name/symbol
    token = top_tokens.results[0]
    assert hasattr(token, 'address')
    assert hasattr(token, 'chain')
    assert hasattr(token, 'price_usd')
    assert hasattr(token, 'volume_usd_24h')
    # `tokens` remains as a backward-compatible alias for `results`
    assert top_tokens.tokens == top_tokens.results

def test_tokens_get_top_with_sort(client, test_data):
    """Test getting top tokens with custom sorting."""
    top_tokens = client.tokens.get_top(
        test_data["ethereum_network"],
        order_by="volume_24h",
        sort="asc",
        limit=3
    )
    assert top_tokens is not None
    assert hasattr(top_tokens, 'results')

# Token Filter API tests
def test_tokens_filter(client, test_data):
    """Test token filtering with volume constraint."""
    filtered = client.tokens.filter(
        test_data["ethereum_network"],
        volume_24h_min=100000,
        limit=5
    )
    assert filtered is not None
    assert hasattr(filtered, 'results')
    # Cursor-based pagination: has_next_page / next_cursor, not page_info
    assert hasattr(filtered, 'has_next_page')
    assert hasattr(filtered, 'next_cursor')
    assert len(filtered.results) > 0
    # Verify token structure
    token = filtered.results[0]
    assert hasattr(token, 'address')
    assert hasattr(token, 'chain')
    assert hasattr(token, 'price_usd')

def test_tokens_filter_multiple_params(client, test_data):
    """Test token filtering with multiple constraints."""
    filtered = client.tokens.filter(
        test_data["ethereum_network"],
        volume_24h_min=100000,
        fdv_min=1000000,
        sort_by="volume_24h",
        sort_dir="desc",
        limit=3
    )
    assert filtered is not None
    assert hasattr(filtered, 'results')

# Multi Prices API tests
def test_tokens_get_multi_prices(client, test_data):
    """Test getting batch prices for multiple tokens."""
    prices = client.tokens.get_multi_prices(
        test_data["ethereum_network"],
        tokens=[
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            test_data["test_token_address"],  # USDC
        ]
    )
    assert prices is not None
    assert isinstance(prices, list)
    assert len(prices) == 2
    # Verify price structure
    price = prices[0]
    assert hasattr(price, 'id')
    assert hasattr(price, 'chain')
    assert hasattr(price, 'price_usd')

def test_tokens_get_multi_prices_single(client, test_data):
    """Test batch prices with a single token."""
    prices = client.tokens.get_multi_prices(
        test_data["ethereum_network"],
        tokens=[test_data["test_token_address"]]
    )
    assert prices is not None
    assert isinstance(prices, list)
    assert len(prices) == 1

def test_tokens_get_multi_prices_validation(client, test_data):
    """Test that empty tokens list raises ValueError."""
    with pytest.raises(ValueError):
        client.tokens.get_multi_prices(test_data["ethereum_network"], tokens=[])

# Search API tests
def test_search_search(client):
    search_results = client.search.search("Jockey")
    assert search_results is not None
    assert hasattr(search_results, 'tokens')
    assert hasattr(search_results, 'pools')
    assert hasattr(search_results, 'dexes')

# Ensure the main function still works when script is run directly
if __name__ == "__main__":
    # Create client
    client = DexPaprikaClient()
    test_data = {
        "ethereum_network": "ethereum",
        "test_pool_network": "ethereum",
        "test_pool_address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        "test_dex": "uniswap_v3",
        "test_token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d"),
    }
    
    # Run all test functions
    print("Running tests manually...")
    test_functions = [
        test_networks_list,
        test_networks_list_dexes,
        test_utils_get_stats,
        test_pools_list_deprecated,
        test_pools_list_by_network_primary,
        test_dexes_list,
        test_pools_list_by_dex,
        test_pools_get_details,
        test_pools_get_ohlcv,
        test_pools_get_transactions,
        test_pools_filter,
        test_pools_filter_multiple_params,
        test_tokens_get_details,
        test_tokens_get_pools,
        test_tokens_get_pools_deprecated_params,
        test_tokens_get_top,
        test_tokens_get_top_with_sort,
        test_tokens_filter,
        test_tokens_filter_multiple_params,
        test_tokens_get_multi_prices,
        test_tokens_get_multi_prices_single,
        test_search_search,
    ]
    
    success_count = 0
    failure_count = 0
    
    for test_func in test_functions:
        print(f"Testing {test_func.__name__}...")
        try:
            if test_func.__name__ in ["test_networks_list", "test_utils_get_stats", "test_pools_list_deprecated", "test_search_search"]:
                test_func(client)
            else:
                test_func(client, test_data)
            print(f"✅ {test_func.__name__} - SUCCESS")
            success_count += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} - FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            failure_count += 1
    
    # Print summary
    print("\n" + "-" * 50 + "\n")
    print(f"SUMMARY: {success_count} endpoints succeeded, {failure_count} endpoints failed")
    print("\n" + "-" * 50 + "\n")
    
    if failure_count > 0:
        sys.exit(1)
    else:
        print("All endpoints tested successfully!") 