import dataclasses as dc
import json
from typing import Any, Callable

from apscheduler.events import JobExecutionEvent
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ADDED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MODIFIED,
)

from emoti_news.dtypes import Counties, Categories, JobSpec
from emoti_news.loggers import backend_logger as log

_JOB_STORE = {"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}
_EXECUTORS = {"processpool": ProcessPoolExecutor(5)}
_JOB_DEFAULTS = {"coalesce": False, "max_instances": 3}

scheduler = BackgroundScheduler(jobstores=_JOB_STORE, executors=_EXECUTORS, job_defaults=_JOB_DEFAULTS, timezone=utc)

# Simple in-memory run logs for jobs (keeps last N runs per job)
RUN_LOGS: dict[str, list[dict]] = {}
MAX_RUNS_PER_JOB = 50


def log_run(job_id: str, status: str, detail: dict):
    RUN_LOGS.setdefault(job_id, [])
    RUN_LOGS[job_id].insert(
        0,
        {
            "ts": detail.get("ts") if "ts" in detail else __import__("time").time(),
            "status": status,
            "detail": detail,
        },
    )
    if len(RUN_LOGS[job_id]) > MAX_RUNS_PER_JOB:
        RUN_LOGS[job_id].pop()


def _on_completion(event: JobExecutionEvent):
    # record run and log
    if event.exception:
        log.error(f"Job {event.job_id} failed: {event.exception}")
        log_run(
            event.job_id,
            "error",
            {"exception": str(event.exception), "ts": __import__("time").time()},
        )
    else:
        log.info(f"Job {event.job_id} succeeded: {event.retval}")
        log_run(
            event.job_id,
            "success",
            {"retval": event.retval, "ts": __import__("time").time()},
        )


def _on_job_added(event: JobExecutionEvent):
    log.debug(f"Job {event.job_id} added")


def _on_job_modified(event: JobExecutionEvent):
    log.debug(f"Job {event.job_id} modified")


scheduler.add_listener(_on_completion, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.add_listener(_on_job_added, EVENT_JOB_ADDED)
scheduler.add_listener(_on_job_modified, EVENT_JOB_MODIFIED)


def add_fetch_news_job(job_id: str = "fetch_news_job") -> JobSpec:
    from emoti_news.backend import get_entrypoint

    entrypoint = get_entrypoint()

    job_spec = JobSpec(
        id=job_id,
        trigger=CronTrigger.from_crontab("1 0,6,12,18 * * *"),
        job_func=entrypoint,
        job_kwargs={
            "countries": Counties.to_list(),
            "categories": Categories.to_list(),
        },
    )

    scheduler.add_job(
        job_spec.job_func,
        trigger=job_spec.trigger,
        id=job_spec.id,
        kwargs=job_spec.job_kwargs,
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    return job_spec


def _log_it(msg: str):
    log.info(msg)


def add_trial_job(job_id: str = "test_job") -> JobSpec:
    job_spec = JobSpec(
        id=job_id,
        trigger=CronTrigger.from_crontab("*/1 * * * *"),
        job_func=_log_it,
        job_args=["Test  Job!"],
    )

    scheduler.add_job(
        job_spec.job_func,
        trigger=job_spec.trigger,
        id=job_spec.id,
        args=job_spec.job_args,
        replace_existing=True,
        **job_spec.scheduler_kwargs,
    )

    return job_spec


JOB_MAP = {"trial_job": add_trial_job, "fetch_news_job": add_fetch_news_job}
