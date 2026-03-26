"""
Tests for scheduler.py.

We test run_spiders() in isolation by patching subprocess.run so no actual
Scrapy processes are launched, and we test setup_schedule() by inspecting
the registered jobs on the schedule library's default scheduler.
"""
import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest
import schedule as _schedule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_scheduler():
    """Import (or re-import) the scheduler module cleanly."""
    sys.modules.pop("scheduler", None)
    import scheduler as mod
    return mod


# ---------------------------------------------------------------------------
# run_spiders()
# ---------------------------------------------------------------------------

class TestRunSpiders:
    @pytest.fixture(autouse=True)
    def mod(self):
        return _import_scheduler()

    def test_calls_scrapy_for_each_spider(self, mod):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            mod.run_spiders()

        called_spiders = [c.args[0][2] for c in mock_run.call_args_list]
        assert called_spiders == mod.SPIDERS

    def test_all_spiders_run_even_if_one_fails(self, mod):
        def side_effect(cmd, **kwargs):
            return MagicMock(returncode=1 if cmd[2] == "ndrc" else 0)

        with patch("subprocess.run", side_effect=side_effect):
            mod.run_spiders()  # must not raise

        # If we reach here without exception, all spiders were attempted

    def test_uses_scrapy_project_dir_as_cwd(self, mod):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            mod.run_spiders()

        for c in mock_run.call_args_list:
            assert c.kwargs.get("cwd") == mod.SCRAPY_PROJECT_DIR

    def test_scrapy_crawl_command_format(self, mod):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            mod.run_spiders()

        cmd = mock_run.call_args_list[0].args[0]
        assert cmd[:2] == ["scrapy", "crawl"]
        assert cmd[2] == mod.SPIDERS[0]

    def test_returns_normally_when_all_succeed(self, mod):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            mod.run_spiders()  # should not raise

    def test_returns_normally_when_all_fail(self, mod):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            mod.run_spiders()  # should still not raise


# ---------------------------------------------------------------------------
# setup_schedule()
# ---------------------------------------------------------------------------

class TestSetupSchedule:
    @pytest.fixture(autouse=True)
    def clean_schedule(self):
        _schedule.clear()
        yield
        _schedule.clear()

    def test_default_registers_one_daily_job(self):
        mod = _import_scheduler()
        with patch.dict("os.environ", {"SCRAPE_TIME": "02:00", "SCRAPE_INTERVAL_HOURS": ""}):
            mod.setup_schedule()
        assert len(_schedule.get_jobs()) == 1

    def test_scrape_time_is_respected(self):
        mod = _import_scheduler()
        with patch.dict("os.environ", {"SCRAPE_TIME": "04:30", "SCRAPE_INTERVAL_HOURS": ""}):
            mod.setup_schedule()
        jobs = _schedule.get_jobs()
        assert len(jobs) == 1
        # schedule stores the time in the repr of the job
        assert "04:30" in repr(jobs[0])

    def test_interval_hours_registers_hourly_job(self):
        mod = _import_scheduler()
        with patch.dict("os.environ", {"SCRAPE_INTERVAL_HOURS": "6"}):
            mod.setup_schedule()
        jobs = _schedule.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].interval == 6

    def test_invalid_interval_hours_falls_back_to_daily(self):
        mod = _import_scheduler()
        with patch.dict("os.environ", {"SCRAPE_INTERVAL_HOURS": "not-a-number", "SCRAPE_TIME": "02:00"}):
            mod.setup_schedule()
        jobs = _schedule.get_jobs()
        assert len(jobs) == 1
        assert "02:00" in repr(jobs[0])

    def test_setup_clears_previous_jobs(self):
        mod = _import_scheduler()
        with patch.dict("os.environ", {"SCRAPE_INTERVAL_HOURS": "", "SCRAPE_TIME": "01:00"}):
            mod.setup_schedule()
        with patch.dict("os.environ", {"SCRAPE_INTERVAL_HOURS": "", "SCRAPE_TIME": "02:00"}):
            mod.setup_schedule()
        # Only one job (the second one), not two
        assert len(_schedule.get_jobs()) == 1
