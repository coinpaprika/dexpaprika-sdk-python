# Caching and Retry Features

This document provides detailed information about the caching and retry features in the DexPaprika SDK.

## Caching System

The SDK includes an intelligent caching system that helps reduce API calls and improve performance.

### How Caching Works

1. By default, all GET requests are cached with expiration times based on the type of data:
   - Network data: 24 hours (rarely changes)
   - Pool data: 5 minutes (changes frequently)
   - Token data: 10 minutes (changes moderately)
   - Statistics: 15 minutes (changes moderately)
   - Other data: 5 minutes (default)

2. The cache is keyed based on both the endpoint and query parameters, ensuring that unique requests get unique cache entries.

3. Cached results are automatically invalidated after their TTL (Time To Live) expires, ensuring you don't receive stale data.

### Using the Caching Features

#### Basic Caching

Caching happens automatically - you don't need to do anything special:

```python
from dexpaprika_sdk import DexPaprikaClient

client = DexPaprikaClient()

# First call hits the API (slower)
networks = client.networks.list()

# Second call uses cached data (much faster)
networks_again = client.networks.list()
```

#### Skipping the Cache

When you need fresh data, you can bypass the cache:

```python
# Force fresh data by skipping the cache
fresh_data = client.networks._get("/networks", skip_cache=True)
```

#### Custom TTL

Advanced usage allows you to set a custom TTL for specific requests:

```python
from datetime import timedelta

# Cache this response for only 30 seconds
short_lived_data = client.networks._get(
    "/networks", 
    ttl=timedelta(seconds=30)
)

# Cache this response for a day
long_lived_data = client.pools._get(
    "/networks/ethereum/pools", 
    ttl=timedelta(days=1)
)
```

#### Clearing the Cache

You can clear the entire cache or just parts of it:

```python
# Clear all cached data
client.clear_cache()

# Clear only network-related cached data
client.clear_cache(endpoint_prefix="/networks")
```

### Technical Details

The caching system uses a dictionary-based in-memory cache with the following components:

1. **CacheEntry Class**: Stores data and expiration time
2. **Cache Key Generation**: Creates unique MD5 hash-based keys for each request
3. **TTL Management**: Different TTLs based on data type
4. **Parameterized Caching**: Supports caching requests with different parameters

## Retry with Backoff

The SDK automatically retries failed API requests with exponential backoff to handle transient errors.

### How Retry Works

1. When an API request fails, the SDK evaluates if the error is retryable:
   - Connection errors (network issues) → Retry
   - Timeouts → Retry
   - Server errors (HTTP 500-599) → Retry
   - Client errors (HTTP 400-499) → Don't retry

2. If the error is retryable, the SDK will:
   - Wait for a specified backoff time
   - Add some random jitter to prevent thundering herd problems
   - Retry the request
   - Repeat until success or max retries is reached

3. Default backoff times:
   - 1st retry: 100ms
   - 2nd retry: 500ms
   - 3rd retry: 1000ms (1 second)
   - 4th retry: 5000ms (5 seconds)

### Configuring Retry Behavior

You can customize the retry behavior when creating the client:

```python
from dexpaprika_sdk import DexPaprikaClient

# Default settings
default_client = DexPaprikaClient()

# Custom retry settings
custom_client = DexPaprikaClient(
    max_retries=3,  # Maximum 3 retry attempts
    backoff_times=[0.2, 1.0, 3.0]  # Custom backoff times in seconds
)

# Disable retries entirely
no_retry_client = DexPaprikaClient(max_retries=0)
```

### When to Use Custom Retry Settings

- **High-throughput applications**: You might want to use shorter backoff times
- **Background jobs**: You might want more retries with longer backoff times
- **User-facing applications**: Balance between responsiveness and reliability

### Error Handling with Retries

Even with retries, some requests may still fail. Always implement proper error handling:

```python
try:
    # This will retry automatically on retryable errors
    response = client.pools.list(limit=5)
except Exception as e:
    # Handle the error after all retries have failed
    print(f"Request failed after retries: {e}")
```

## Performance Considerations

1. **Memory Usage**: The caching system stores responses in memory. For applications processing large amounts of data, monitor memory usage.

2. **Request Latency**: Retries can increase the total time a request takes to complete or fail. Set appropriate timeouts for your application.

3. **API Rate Limits**: While retries and caching can help manage rate limits, they don't completely solve the problem. Be aware of your API usage.

## Best Practices

1. **Cache Invalidation**: Clear specific parts of the cache when you know the data has changed.

2. **Configure Retries Appropriately**: Don't set extremely long retry sequences for user-facing applications.

3. **Monitoring**: Track cache hit rates and retry counts to optimize your configuration.

4. **Error Handling**: Always implement proper error handling regardless of retry mechanisms.

5. **Testing**: Test your application's behavior when the API is slow or unavailable to ensure graceful degradation. 