# import asyncio
# import os
# from functools import cache
# from string import Template
# from typing import Any, Dict, List, Literal, Callable

from fastapi import FastAPI, HTTPException

# from pydantic import BaseModel
# from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent

from emoti_news.jobs import scheduler, JOB_MAP

# from emoti_news.loggers import backend_logger as log
from .apis.jobs import jobs as jobs_router
from .apis.sched import sched as sched_router

# def entrypoint_job(job_id: str, country: str = "us", category: str = "general"):
#     # Example sync client; if your client is async, use wrapper below.
#     # from emoti_news.backend.api.ext_newsapi import API
#     # client = API()
#     # return client.get_top_headlines(country=country, category=category)
#     print(f"[{job_id}] fetching news for {country}:{category}")
#     return {"job_id": job_id, "country": country, "category": category, "status": "ok"}


# # If you need to run an async function with BackgroundScheduler, run a wrapper:
# def run_async_func(coro_func, *args, **kwargs):
#     # Run coroutine in a new event loop; safe for background scheduler threads.
#     loop = asyncio.new_event_loop()
#     try:
#         return loop.run_until_complete(coro_func(*args, **kwargs))
#     finally:
#         loop.close()

#
# # In-memory run logs for UI monitoring
# RUN_LOGS: Dict[str, List[Dict[str, Any]]] = {}
# MAX_RUNS_PER_JOB = 50


# def log_run(job_id: str, status: str, detail: Dict[str, Any]):
#     RUN_LOGS.setdefault(job_id, [])
#     RUN_LOGS[job_id].insert(0, {"status": status, "detail": detail})
#     if len(RUN_LOGS[job_id]) > MAX_RUNS_PER_JOB:
#         RUN_LOGS[job_id].pop()
#
#
# # Event handler to keep run logs
# def _on_job_event(event: JobExecutionEvent):
#     if event.exception:
#         log_run(event.job_id, "error", {"exception": str(event.exception)})
#     else:
#         log_run(event.job_id, "success", {"retval": event.retval})
#

# scheduler.add_listener(_on_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# ------------- FastAPI App -------------
app = FastAPI(title="Emoti News Scheduler")

app.include_router(router=jobs_router)
app.include_router(router=sched_router)


@app.on_event("startup")
async def startup_event():
    # Only for testing
    scheduler.start()

    for job_id, job_spec in JOB_MAP.items():
        job_spec()


# class JobSpec(BaseModel):
#     id: str
#     cron: str  # e.g. '0 8 * * *'
#     args: List[Any] = []
#     kwargs: Dict[str, Any] = {}
#     replace_existing: bool = False


# class JobAdmin:
#     def __init__(self, job_id: str):
#         self.job_id = job_id
#
#     @staticmethod
#     def _get_job_func_by_job_id(job_id: str) -> Callable | None:
#         return {
#             "trial_job": add_trial_job,
#         }.get(job_id)
#
#     @staticmethod
#     def _is_job_running(job_id: str) -> bool:
#         return scheduler.get_job(job_id) is not None
#
#     def run_job_or_throw(self, job_id: str) -> JobSpec:
#         if job_func := self._get_job_func_by_job_id(job_id):
#             try:
#                 return job_func()
#             except Exception as e:
#                 raise HTTPException(status_code=400, detail=f"Failed to run job: {e}")
#         else:
#             raise HTTPException(status_code=400, detail=f"unknown job id: {self.job_id}")
#
#     def add(self):
#         log.info(f"adding job: {self.job_id}")
#
#         if self._is_job_running(self.job_id):
#             raise HTTPException(status_code=400, detail="job already exists")
#
#         status = self.run_job_or_throw(self.job_id)
#         log_run(self.job_id, "scheduled", status.as_dict())
#
#         return {"created": self.job_id}


# @app.get("/jobs", summary="Start or shutdown the scheduler")
# async def jobs_status(api_key: str, action: Literal["start", "shutdown", "status"]):
#     if not _is_api_key_valid(api_key):
#         raise HTTPException(status_code=403, detail="Access denied. Invalid API key")
#
#     if action == "start":
#         if scheduler.running:
#             return {"status": "already_running"}
#         scheduler.start()
#         return {"status": "started"}
#     elif action == "status":
#         return {"is_running": scheduler.running}
#     else:
#         if scheduler.running:
#             scheduler.shutdown(wait=False)
#             return {"status": "shutdown"}
#         return {"status": "not_running"}


# def _get_job_func_by_job_id(job_id: str) -> Callable | None:
#     return {
#         "trial_job": add_trial_job,
#         "fetch_news_job":add_fetch_news_job
#     }.get(job_id)


# @app.post("/jobs/add", status_code=201)
# def create_job(job_id: str):
#     log.info(f"Adding job: {job_id}")
#     if scheduler.get_job(job_id):
#         raise HTTPException(status_code=400, detail="job already exists")
#
#     if job_func := _get_job_func_by_job_id(job_id):
#         try:
#             status = job_func()
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=f"Failed to run job: {e}")
#     else:
#         raise HTTPException(status_code=400, detail=f"unknown job id: {job_id}")
#
#     log_run(job_id, "scheduled", status.as_dict())
#     return {"created": job_id}
#
#
# @app.get("/jobs/list")
# def list_jobs():
#     out = []
#     for job in scheduler.get_jobs():
#         out.append(
#             {
#                 "id": job.id,
#                 "next_run_time": getattr(job, "next_run_time", ""),
#                 "trigger": str(job.trigger),
#                 "paused": getattr(job, "paused", False),
#             }
#         )
#     return out
#
#
# @app.get("/jobs/get/")
# def get_job(job_id: str):
#     j = scheduler.get_job(job_id)
#     if not j:
#         raise HTTPException(status_code=404, detail="not found")
#     return {
#         "id": j.id,
#         "next_run_time": str(j.next_run_time),
#         "trigger": str(j.trigger),
#     }
#
#
# @app.post("/jobs/admin/")
# def admin_job(
#     api: str, action: Literal["pause", "resume", "delete"], job_id: str
# ):
#     if not _is_api_key_valid(api):
#         raise HTTPException(status_code=403, detail="Access denied. Invalid API key")
#
#     log.info(f"Admin action: {action} job: {job_id}")
#
#     job = scheduler.get_job(job_id)
#
#     if job:
#         print(f">>>> {job}")
#     else:
#         print(scheduler.get_jobs())
#
#     if not job:
#         raise HTTPException(status_code=404, detail=f"job '{job_id}' not found")
#
#     if action == "delete":
#         scheduler.remove_job(job_id)
#     elif action == "pause":
#         job.pause()
#     elif action == "resume":
#         job.resume()
