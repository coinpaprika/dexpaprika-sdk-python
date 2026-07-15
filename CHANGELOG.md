# Changelog

All notable changes to the DexPaprika SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-07-15

### Breaking Changes
- **API endpoint removed (410 Gone)**: `GET /networks/{network}/tokens/{address}/pools`
  was removed by DexPaprika. `tokens.get_pools()` now calls the unified
  `/networks/{network}/pools/search` endpoint with its new `token_address`
  parameter. The method signature is unchanged.
- **Response shape changed**: `tokens.get_pools()` now returns the
  cursor-paginated `PoolSearchResponse` (rows under `results` plus
  `has_next_page` / `next_cursor`; `.pools` remains a backward-compatible alias
  for `.results`). `page` is accepted but ignored; pass `cursor=...` to page.
- **Network-scoped only**: the cross-network `/pools/search` endpoint accepts
  `token_address` but silently ignores it, so `get_pools()` still requires a
  network.
- **Deprecated parameters**: `address` (pair queries) and `reorder`
  (pair-perspective flip) have no `/pools/search` equivalent. They now emit a
  `DeprecationWarning` and are not sent; repeating `token_address` on the API
  side is last-wins, not a pair filter. Filter the returned pools client-side
  to match a pair.
- Legacy `order_by` values (such as `volume_usd`) are mapped to the canonical
  search names automatically; an unknown token address returns an empty result
  set, not an error.

## [0.5.1] - 2026-07-01

### Added
- **`DeprecatedEndpointError`**: when the API returns an error whose body carries a `replacement` field, the client now raises this typed exception (subclass of `DexPaprikaError`) with the API message + `Use <replacement> instead.`, and `.replacement` / `.api_message` / `.status_code` accessors, instead of a bare `requests.HTTPError`. Not retried. Generic across any error status carrying a `replacement`.

## [0.5.0] - 2026-06-30

### Breaking Changes
- **API endpoints removed (410 Gone)**: `/networks/{network}/pools`,
  `/networks/{network}/pools/filter`, `/networks/{network}/tokens/top` and
  `/networks/{network}/tokens/filter` were removed by DexPaprika. The SDK now
  uses the unified `/networks/{network}/pools/search` and
  `/networks/{network}/tokens/search` endpoints.
- **Response shape changed**: `pools.list_by_network()`, `pools.list()`,
  `pools.filter()`, `tokens.get_top()` and `tokens.filter()` now return
  cursor-paginated responses with rows under `results` plus `has_next_page` and
  `next_cursor` (no more `page_info`). `.pools` / `.tokens` remain as
  backward-compatible aliases for `.results`.
- **Item fields changed**: pool items use `id` (pool address), `volume_usd_24h`,
  `volume_usd_7d`, `volume_usd_30d`, `liquidity_usd`, `transactions_24h`,
  `price_usd`, `price_change_percentage_5m/1h/24h`. Token items are flat and use
  `address`, `price_usd`, `volume_usd_24h/7d/30d`, `liquidity_usd`, `fdv_usd`,
  `txns_24h`, `price_change_percentage_24h` (no `name`/`symbol`, no nested time
  metrics).
- Removed `TopTokenTimeMetrics` (no analog in the flat search shape).

### Changed
- Method signatures are unchanged for backward compatibility. Legacy `order_by` /
  `sort_by` values (e.g. `volume_usd`, `volume_24h`, `transactions`, `fdv`) and
  legacy filter param names (e.g. `volume_24h_min`) are mapped to the canonical
  search names automatically; unknown sort fields fall back to `volume_usd_24h`.
- `page` is still accepted but ignored (the search endpoints are cursor-based); a
  new optional `cursor` parameter was added to the migrated methods.
- `order_by` is no longer validated against a fixed enum (unknown values map to a
  default instead of raising).
- New Pydantic models: `PoolSearchToken`, `PoolSearchResult`, `PoolSearchResponse`,
  `TokenSearchResult`, `TokenSearchResponse`. `FilteredPool`, `PoolFilterResponse`,
  `TopToken`, `TopTokensResponse`, `FilteredToken` and `TokenFilterResponse` are
  retained as aliases of the new models.
- Updated SDK version to 0.5.0 and the user agent string.

### Unchanged
- DEX pools (`dexes`/`pools.list_by_dex`), pool detail, OHLCV, transactions, token
  pools, token detail, multi/prices, search, networks, dexes and stats endpoints
  are untouched.

## [0.4.0] - 2026-03-31

### Added
- **Pool filtering**: `pools.filter()` method for advanced pool filtering by volume, liquidity, transactions, and creation date on any network
- **Top tokens**: `tokens.get_top()` method for discovering top tokens on a network ranked by volume, price, liquidity, or other metrics
- **Token filtering**: `tokens.filter()` method for filtering tokens by volume, liquidity, FDV, transactions, and creation date
- **Batch prices**: `tokens.get_multi_prices()` method for getting prices of up to 10 tokens in a single request
- New Pydantic models: `PoolFilterResponse`, `TopToken`, `TopTokenTimeMetrics`, `TopTokensResponse`, `FilteredToken`, `TokenFilterResponse`, `TokenPrice`
- Optional `volume_usd_7d`, `liquidity_usd` fields on `Pool` model
- Optional `type`, `status`, `has_image` fields on `Token` model
- Tests for all new endpoints

### Changed
- Updated SDK version to 0.4.0
- Updated user agent string
- Migrated Pydantic models from deprecated `class Config` to `ConfigDict`
- Updated README with new endpoint examples and documentation

## [0.3.0] - 2025-01-27

### Breaking Changes
- **DEPRECATED**: Global pools method `pools.list()` due to DexPaprika API v1.3.0 changes
- **MIGRATION REQUIRED**: The global `/pools` endpoint now returns `410 Gone`
- All pool operations now require network specification for better performance

### Added
- Automatic fallback for deprecated `pools.list()` method to Ethereum network
- New `reorder` parameter in `tokens.get_pools()` method for reordering pool metrics
- Comprehensive deprecation warnings with migration guidance
- Enhanced error handling for `410 Gone` responses

### Changed
- Updated SDK version to 0.3.0 to reflect API compatibility with DexPaprika v1.3.0
- Improved documentation with migration examples
- Updated user agent string to match new SDK version

### Migration Guide
```python
# Before (deprecated):
pools = client.pools.list()

# After (recommended):
pools = client.pools.list_by_network('ethereum')
pools = client.pools.list_by_network('solana')
pools = client.pools.list_by_network('fantom')

# Token pools with reordering (new feature):
pools = client.tokens.get_pools(
    network_id="ethereum",
    token_address="0x...",
    reorder=True  # Makes the specified token primary for all metrics
)
```

## [0.2.0] - 2024-07-01

### Added
- Retry with exponential backoff mechanism for API requests
  - Automatic retry for connection errors, timeouts, and server errors (5xx)
  - Configurable retry count and backoff times
  - Default backoff times: 100ms, 500ms, 1s, and 5s with random jitter
- TTL-based caching system
  - Intelligent caching with different TTLs for different types of data
  - Support for caching parameterized requests
  - Skip cache option to force fresh data
  - Cache clearing functionality
- Example code demonstrating new features
- Unit tests for caching and retry functionality

### Changed
- Updated documentation to reflect new features
- Improved error handling for API requests

## [0.1.0] - 2024-06-01

### Added
- Initial release of the DexPaprika SDK
- Support for all DexPaprika API endpoints
- Type-safe response models using Pydantic
- Parameter validation
- API services: Networks, Pools, Tokens, DEXes, Search, Utils
- Basic examples
- Unit tests 