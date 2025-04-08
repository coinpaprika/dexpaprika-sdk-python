import time
from functools import wraps
from typing import Dict, Any, Callable, Optional

# perf tracking dict
_perf_stats = {}

def track_perf(func=None, *, name: Optional[str] = None):
    """tracking decorator for api calls"""
    def decorator(f):
        func_name = name or f.__name__
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            # track time
            start = time.time()
            result = f(*args, **kwargs)
            end = time.time()
            
            # update stats
            if func_name not in _perf_stats:
                _perf_stats[func_name] = {
                    'calls': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0
                }
            
            elapsed = end - start
            stats = _perf_stats[func_name]
            stats['calls'] += 1
            stats['total_time'] += elapsed
            stats['min_time'] = min(stats['min_time'], elapsed)
            stats['max_time'] = max(stats['max_time'], elapsed)
            
            return result
        
        return wrapper
    
    if func:
        return decorator(func)
    return decorator

def get_perf_stats() -> Dict[str, Any]:
    """get current perf stats"""
    # add avg time
    stats = {}
    for name, data in _perf_stats.items():
        stats[name] = {**data}
        if data['calls'] > 0:
            stats[name]['avg_time'] = data['total_time'] / data['calls']
    
    return stats

def reset_perf_stats() -> None:
    """reset stats"""
    global _perf_stats
    _perf_stats = {} 