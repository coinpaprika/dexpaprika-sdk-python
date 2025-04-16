# Changelog

All notable changes to the DexPaprika SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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