import os
import shutil
import time
import tempfile
from emoti_news.utils import dcache


def test_dcache_basic():
    temp_dir = tempfile.mkdtemp()
    calls = []

    @dcache(temp_dir, ttl_minutes=1)
    def add(x, y):
        calls.append((x, y))
        return x + y

    # First call, should compute
    assert add(1, 2) == 3
    assert calls == [(1, 2)]
    # Second call, should use cache
    assert add(1, 2) == 3
    assert calls == [(1, 2)]
    # Different args, should compute
    assert add(2, 3) == 5
    assert calls == [(1, 2), (2, 3)]
    shutil.rmtree(temp_dir)


def test_dcache_ttl_expiry():
    temp_dir = tempfile.mkdtemp()
    calls = []

    @dcache(temp_dir, ttl_minutes=0.001)  # very short TTL
    def mul(x, y):
        calls.append((x, y))
        return x * y

    assert mul(2, 3) == 6
    assert calls == [(2, 3)]
    # Should use cache
    assert mul(2, 3) == 6
    assert calls == [(2, 3)]
    # Wait for cache to expire
    time.sleep(1)
    assert mul(2, 3) == 6
    assert calls == [(2, 3), (2, 3)]
    shutil.rmtree(temp_dir)


def test_dcache_kwargs():
    temp_dir = tempfile.mkdtemp()
    calls = []

    @dcache(temp_dir, ttl_minutes=1)
    def concat(a, b=0):
        calls.append((a, b))
        return str(a) + str(b)

    assert concat(1, b=2) == "12"
    assert calls == [(1, 2)]
    # Should use cache regardless of kwarg order
    assert concat(a=1, b=2) == "12"
    assert calls == [(1, 2)]
    shutil.rmtree(temp_dir)
