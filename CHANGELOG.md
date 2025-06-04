# Changelog

All notable changes to the DexPaprika SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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