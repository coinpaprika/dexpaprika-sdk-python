# Changelog

All notable changes to the DexPaprika SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2026-08-14

### Added
- **Optional API key.** `DexPaprikaClient(api_key=...)`, falling back to the `DEXPAPRIKA_API_KEY` environment variable when no argument is given. Keyless remains the default and is unchanged: without a key the client sends exactly what it sent before. The key is transmitted as the **entire** `Authorization` value, with no `Bearer` prefix and no other scheme word, because the API checksums the raw header and a scheme word returns 401.
- The host is never inferred from the presence of a key. Free keys are served from the default `base_url` and only Pro moves to `api-pro.dexpaprika.com`, which callers set through `base_url`. Sending a free key to the Pro host returns 403, so guessing would break exactly the people who just registered.

### Fixed
- **The User-Agent was pinned to `DexPaprika-SDK-Python/0.5.1`** while the package shipped 0.8.0, so every request misreported which version of the SDK sent it. It is now derived from `__version__`. A caller-supplied `user_agent` still wins.

### Notes
- 21 new tests covering the bare-key format against five scheme words, keyless behaviour, argument-beats-environment precedence, whitespace handling, rejection of keys carrying header-injection characters, and the host rules.
- A key the API cannot read is ignored rather than rejected on the data endpoints: the call returns `200` with real data while quietly serving the keyless tier. `/usage` is the only endpoint that reports the truth, and its `plan` field is the way to confirm a key is landing.

## [0.8.0] - 2026-08-14

### Breaking Changes
- **API endpoint removed (410 Gone)**: `GET /networks/{network}/dexes/{dex}/pools`
  was removed by DexPaprika. `pools.list_by_dex()` now calls
  `/networks/{network}/pools/search` with the `dex_name` filter. The `dex_id`
  argument is unchanged and is sent as `dex_name`. Despite the parameter name,
  that filter matches the DEX id (`curve`, `uniswap_v3`) case-insensitively. A
  display name such as `Uniswap V3` returns an empty result set instead of an
  error, so pass the `dex_id` field from `GET /networks/{network}/dexes`.
- **Response shape changed**: `pools.list_by_dex()` now returns the
  cursor-paginated `PoolSearchResponse` (rows under `results` plus
  `has_next_page` / `next_cursor`; `.pools` remains a backward-compatible alias
  for `.results`). There is no `page_info`. `page` is accepted but ignored;
  pass `cursor=...` to page.
- **Field renames on pool rows**: the 24h volume is `volume_usd_24h`, not
  `volume_usd`, and the transaction count is `transactions_24h`, not
  `transactions`.
- `order_by` is no longer validated against `VALID_ORDER_BY_VALUES` on
  `list_by_dex`. Legacy values such as `volume_usd` are mapped to the canonical
  search fields, so canonical names like `liquidity_usd` now work too.

### Fixed
- `PoolSearchToken` matches the wire: tokens inside a search result carry `id`,
  `chain` and `has_image`. `name` and `symbol` are kept as optional fields and
  come back as None.
- Added the missing `price_change_percentage_6h` field to `PoolSearchResult`.
- The `advanced_example.py` DEX section printed `None/None` pairs and a missing
  `volume_usd`. It now labels pools by token id when no symbol is returned.
- The `Dex` model declared the identifier as `id`, but
  `GET /networks/{network}/dexes` returns it as `dex_id`. Every `Dex.id` was
  therefore `None` and the real value was dropped. The field is now `dex_id`,
  and `Dex.id` stays as a read-only alias that returns it. The model also picked
  up `volume_usd_24h`, `txns_24h` and `pools_count`, which the wire has always
  sent and the model silently discarded.
- `advanced_example.py` read `dexes.dexes[0].id`, which was `None`, so
  `list_by_dex()` raised "dex_id is required" before it could make a request.
  It now reads `dex_id`.

## [0.7.0] - 2026-08-07

### Added
- **Short price-change windows on pools**: `/networks/{network}/pools/search`
  now accepts `price_change_percentage_6h`, `price_change_percentage_1h` and
  `price_change_percentage_5m` as `order_by` values. All three were added to
  `POOL_SORT_CANONICAL`, so `pools.list_by_network()` and `pools.filter()` pass
  them through instead of silently falling back to `volume_usd_24h`.
- **Price-change bounds on `pools.filter()`**: eight new keyword arguments,
  `price_change_percentage_{24h,6h,1h,5m}_{min,max}`. The 24h pair was missing
  as well, so all four windows are now filterable. Values are percentages and
  negatives are meaningful: `price_change_percentage_24h_max=-20` selects pools
  down at least 20% on the day.
- **24h price-change bounds on `tokens.filter()`**: two new keyword arguments,
  `price_change_percentage_24h_min` and `_max`.
  `/networks/{network}/tokens/search` applies both, so the SDK now exposes them.
- **`PoolSearchResult.price_change_percentage_6h`**: the search endpoint returns
  this field and the model was dropping it.

### Notes
- The 6h, 1h and 5m windows are pool-only; 24h is not. `/tokens/search` returns
  HTTP 400 when asked to sort by a short window, and token rows carry no 5m
  field, so `TOKEN_SORT_CANONICAL` is deliberately left without those three
  while keeping `price_change_percentage_24h`. A short window passed to a token
  method as a sort field falls back to `volume_usd_24h`. Regression tests pin
  the split on both the sort side and the filter side.
- `/tokens/search` answers 200 to a 6h, 1h or 5m filter bound and then ignores
  it, so `tokens.filter()` does not accept those three. Passing one raises
  `TypeError` rather than returning an unfiltered page that looks filtered.
- An unknown filter param is ignored by the API, which still answers 200 with a
  full unfiltered result set, so a typo in a bound would look like a working
  call returning the wrong pools. The new tests assert against the API's own
  `query` echo, which lists only the parameters it recognised.

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