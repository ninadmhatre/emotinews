import datetime as dt
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import select, text

from emoti_news.database import Status, DB, DBType
from emoti_news.dtypes import JobStatus
from emoti_news.utils import CaptureCallStatus, TimeIt, dcache, get_dcache
from emoti_news.loggers import backend_logger as log

# Test configurations
TEST_DIR = Path(__file__).parent
SQLITE_TEST_DB = TEST_DIR / "test_news.db"
PG_TEST_DB = "test_news"


@pytest.fixture(scope="function")
def sqlite_db():
    """Setup a temporary SQLite database for testing"""
    # Override database configuration
    original_type = DB.db_type
    original_db_cfg = DB.get_db_cfg()

    DB.db_type = DBType.Sqlite
    DB.get_db_cfg = lambda: {"path": SQLITE_TEST_DB}

    # Create tables
    engine = DB.clear_engine().get_engine()
    Status.metadata.create_all(engine)

    yield engine

    # Cleanup
    Status.metadata.drop_all(engine)
    if SQLITE_TEST_DB.exists():
        print(f"Deleting test database {SQLITE_TEST_DB}")
        # SQLITE_TEST_DB.unlink()

    # Restore original config
    DB.db_type = original_type
    DB.get_db_cfg = lambda: original_db_cfg
    DB.clear_engine()


@pytest.fixture(scope="function")
def postgres_db():
    """Setup a temporary PostgreSQL database for testing"""
    original_type = DB.db_type
    original_db_cfg = DB.get_db_cfg()

    DB.db_type = DBType.Postgress
    DB.get_db_cfg = lambda: {**original_db_cfg, "database": PG_TEST_DB}

    engine = DB.clear_engine().get_engine()

    # Create test database
    with engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {PG_TEST_DB}"))
        conn.execute(text(f"CREATE DATABASE {PG_TEST_DB}"))

    Status.metadata.create_all(engine)

    yield engine

    # Cleanup
    Status.metadata.drop_all(engine)
    with engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE {PG_TEST_DB}"))

    # Restore original config
    DB.db_type = original_type
    DB.get_db_cfg = lambda: original_db_cfg
    DB.clear_engine()


class TestCaptureCallStatus:
    def _get_status_by_id(self, job_id: str, sqlite_db):
        with sqlite_db.connect() as conn:
            result = conn.execute(select(Status).where(Status.job_id == job_id)).first()
            return result

    def test_init(self):
        """Test initialization of CaptureCallStatus"""
        mock_date = dt.datetime(2025, 10, 23, 14, 30)
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value = mock_date
            status = CaptureCallStatus("US", "business")

            # Check basic attributes
            assert status.country == "US"
            assert status.category == "business"
            assert status.run_date == mock_date.date()
            assert status.hour_min == "14:30"

            # Check job_id format
            expected_id = f"US.business_{mock_date.strftime('%Y%m%d')}_{mock_date.strftime('%H:%M')}"
            assert status.job_id == expected_id

            # Check meta initialization
            assert isinstance(status.meta, dict)
            assert len(status.meta) == 0

    def test_context_manager_success(self, sqlite_db):
        """Test successful execution of context manager with SQLite"""
        # Use fixed time for consistent testing
        mock_date = dt.datetime(2025, 10, 23, 14, 30)
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value = mock_date
            with CaptureCallStatus("US", "business") as status:
                # Check if status is set to IN_PROGRESS
                result = self._get_status_by_id(status.job_id, sqlite_db)
                assert result is not None, "Status record not found"
                assert result.status == JobStatus.IN_PROGRESS.value

            # Check if status is updated to COMPLETED
            result = self._get_status_by_id(status.job_id, sqlite_db)
            assert result is not None, "Status record not found"
            assert result.status == JobStatus.COMPLETED.value

    def test_context_manager_failure(self, sqlite_db):
        """Test failed execution of context manager with SQLite"""
        mock_date = dt.datetime(2025, 10, 23, 14, 30)
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value = mock_date

            # Capture job_id before raising error
            test_job_id = None
            with pytest.raises(ValueError):
                with CaptureCallStatus("US", "business") as status:
                    test_job_id = status.job_id
                    raise ValueError("Test error")

            assert test_job_id is not None, "Job ID not captured before error"

            # Check if status is updated to FAILED
            result = self._get_status_by_id(test_job_id, sqlite_db)

            assert result is not None, "Failed status record not found"
            assert result.status == JobStatus.FAILED.value
            assert "Test error" in result.meta.get("error", "")

    def test_context_manager_two_contexts(self, sqlite_db):
        """Test failed execution of context manager with SQLite"""
        mock_date = dt.datetime(2025, 10, 23, 14, 30)
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value = mock_date

            with pytest.raises(ValueError):
                with CaptureCallStatus("US", "business") as status_outer:
                    with CaptureCallStatus("US", "business") as status_inner:
                        time.sleep(0.5)  # Simulate some work

                    # check inner status

                    assert status_inner.job_id == status_outer.job_id, "Jobs ID should match!"

                    result = self._get_status_by_id(status_inner.job_id, sqlite_db)
                    assert result is not None, "Failed status record not found"
                    assert result.status == JobStatus.COMPLETED.value

                    raise ValueError("Outer Failed")

            # Check if status is updated to FAILED
            result = self._get_status_by_id(status_inner.job_id, sqlite_db)
            assert result is not None, "Failed status record not found"
            assert result.status == JobStatus.FAILED.value
            assert "Outer Failed" in result.meta.get("error", "")

    @pytest.mark.skip(reason="PostgreSQL tests are disabled")
    def test_postgres_context_manager(self, postgres_db):
        """Test context manager with PostgreSQL"""
        mock_date = dt.datetime(2025, 10, 23, 14, 30)
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value = mock_date
            with CaptureCallStatus("US", "business") as status:
                # Check if status is set to IN_PROGRESS
                with postgres_db.connect() as conn:
                    result = conn.execute(select(Status).where(Status.job_id == status.job_id)).first()
                    assert result is not None, "Status record not found"
                    assert result.status == JobStatus.IN_PROGRESS.value


class TestTimeIt:
    def test_elapsed_time(self):
        """Test basic timing functionality"""
        sleep_time = 0.1
        with TimeIt() as timer:
            time.sleep(sleep_time)

        assert sleep_time < timer.elapsed < sleep_time + 0.1
        assert sleep_time * 1000 < timer.elapsed_ms < (sleep_time + 0.1) * 1000

    def test_named_timer(self):
        """Test timer with custom name"""
        timer_name = "TestTimer"
        with TimeIt(timer_name) as timer:
            time.sleep(0.1)

        assert timer.name == timer_name
        assert str(timer).startswith(timer_name)

    def test_callback(self):
        """Test timer callback functionality"""
        callback_called = False
        callback_time = 0.0

        def callback(elapsed: float):
            nonlocal callback_called, callback_time
            callback_called = True
            callback_time = elapsed

        with TimeIt(callback=callback):
            time.sleep(0.1)

        assert callback_called
        assert callback_time > 0

    def test_nested_timers(self):
        """Test nested timer functionality"""
        with TimeIt("outer") as outer:
            time.sleep(0.1)
            with TimeIt("inner") as inner:
                time.sleep(0.1)

        assert outer.elapsed >= 0.2
        assert inner.elapsed >= 0.1
        assert outer.elapsed > inner.elapsed


class Counter:
    def __init__(self):
        self._laps = 0

    def incr(self):
        self._laps += 1

    def incr_by(self, val: int):
        return self._laps == val

    def __enter__(self):
        self._laps = 0
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            raise exc_val


class TestDcache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _dir = tempfile.mkdtemp()
        cls.cache = get_dcache(cache_dir=_dir, ttl=60, enable=1)

    @classmethod
    def setUp(cls):
        cls.cache.create_job()

    @classmethod
    def tearDown(cls):
        cls.cache.clear()

    def test_dcache_basic(self):
        counter = Counter()

        @dcache()
        def add(x, y):
            counter.incr()
            return x + y

        with counter:
            assert add(1, 2) == 3
            assert add(1, 2) == 3
            assert add(2, 3) == 5
            assert add(2, 3) == 5

        assert counter.incr_by(2)

    def test_dcache_kwargs(self):
        counter = Counter()

        @dcache()
        def concat(a, b=0):
            counter.incr()
            return str(a) + str(b)

        with counter:
            assert concat(1, b=2) == "12"
            assert concat(a=1, b=2) == "12"
            assert concat(1) == "10"
            assert concat(1) == "10"

        assert counter.incr_by(2)

    def test_dcache_expiry(self):
        counter = Counter()

        @dcache(ttl=1)
        def mul(x, y):
            counter.incr()
            return x * y

        with counter:
            assert mul(2, 3) == 6
            assert mul(2, 3) == 6
            assert mul(3, 4) == 12
            assert mul(2, 3) == 6
            assert mul(3, 4) == 12

            time.sleep(1.1)

            assert mul(2, 3) == 6
            assert mul(3, 4) == 12

        assert counter.incr_by(4), f"Actual: {counter._laps}, Expected: 4"

    def test_dcache_all_supported_types(self):
        """Test all supported data types with caching"""
        counter = Counter()

        @dcache()
        def process_value(x):
            counter.incr()
            return x

        # Test with None
        with counter:
            assert process_value(None) is None
            assert process_value(None) is None

        assert counter.incr_by(2)

        # Test with boolean
        values_to_try = [
            True,
            42,
            3.14,
            "test",
            (1, "a", 3.14),
            {"a": 1, "b": [2, 3], "c": {"nested": True}},
            dt.datetime.now(),
            dt.date.today(),
        ]

        for val in values_to_try:
            log.info(f"Testing value: {val}")
            with counter:
                result_1 = process_value(val)
                result_2 = process_value(val)

                assert result_1 == result_2

            assert counter.incr_by(1)

    def test_dcache_skip_list_caching(self):
        """Test that we can skip caching for specific calls"""
        counter = Counter()

        @dcache()
        def process_list(x):
            counter.incr()
            return x

        test_list = [1, 2, 3]

        with counter:
            assert process_list(test_list) == [1, 2, 3]
            assert process_list(test_list) == [1, 2, 3]
            assert process_list(test_list, _skip_cache=True) == [1, 2, 3]
            assert process_list(test_list) == [1, 2, 3]
            assert process_list("test") == "test"
            assert process_list("test") == "test"

        assert counter.incr_by(3)

    def test_dcache_on_method(self):
        class MyClass:
            def __init__(self):
                self.counter = Counter()

            @dcache(is_cls_method=True)
            def compute(self, x, y):
                self.counter.incr()
                return x * y

        obj = MyClass()

        with obj.counter:
            assert obj.compute(2, 5) == 10
            assert obj.compute(2, 5) == 10
            assert obj.compute(y=5, x=2) == 10
            assert obj.compute(3, 4) == 12
            assert obj.compute(3, 4) == 12

        assert obj.counter.incr_by(2)

    def test_dcache_dict_mutation(self):
        """Test that mutating a dictionary after getting it from cache doesn't affect the cached value"""
        counter = Counter()

        @dcache()
        def get_data():
            counter.incr()
            return {"key1": "value1", "nested": {"key2": "value2"}}

        data1 = get_data()
        assert counter.incr_by(1)

        data2 = get_data()
        assert counter.incr_by(1)  # Counter should still be 1

        data2["new_key"] = "new_value"
        data2["nested"]["new_nested_key"] = "new_nested_value"

        data3 = get_data()
        assert counter.incr_by(1)  # Counter should still be 1

        assert data3 == {"key1": "value1", "nested": {"key2": "value2"}}
        assert "new_key" not in data3
        assert "new_nested_key" not in data3["nested"]

        assert data1 is not data2  # Different objects
        assert data1 == data3  # But equal in value
        assert data1 is not data3  # And different objects
