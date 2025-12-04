from typing import Annotated, Any, Literal

from fastapi import Depends, APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from emoti_news.frontend.apis import has_token
from emoti_news.jobs import scheduler, JOB_MAP
from emoti_news.jobs.jobs import RUN_LOGS
from emoti_news.loggers import backend_logger as log

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

jobs = APIRouter(prefix="/jobs", tags=["Jobs"], dependencies=[Depends(has_token)])


@jobs.get("/create")
def create_job(job_id: str):
    log.info(f"Adding job: {job_id}")
    if scheduler.get_job(job_id):
        raise HTTPException(status_code=400, detail="job already exists")

    if job_func := JOB_MAP.get(job_id):
        try:
            job_func()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to run job: {e}")
    else:
        raise HTTPException(status_code=400, detail=f"unknown job id: {job_id}")

    return {"created": job_id}


@jobs.get("/list")
def list_jobs():
    out = []

    for job in sorted(scheduler.get_jobs(), key=lambda j: getattr(j, "id", "")):
        runs = RUN_LOGS.get(job.id, [])
        last_status = runs[0]["status"] if runs else None
        last_ts = runs[0]["ts"] if runs else None
        out.append(
            {
                "id": job.id,
                "next_run_time": getattr(job, "next_run_time", ""),
                "trigger": str(job.trigger),
                "paused": getattr(job, "next_run_time", None) is None,
                "run_count": len(runs),
                "last_status": last_status,
                "last_run": last_ts,
            }
        )
    return out


@jobs.get("/admin")
def admin_jobs(action: Literal["pause", "resume", "delete"], job_id: str):
    job = scheduler.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"job '{job_id}' not found")

    if action == "delete":
        scheduler.remove_job(job_id)
    elif action == "pause":
        scheduler.pause_job(job_id)
    elif action == "resume":
        scheduler.resume_job(job_id)


@jobs.post("/jobs/register")
@jobs.get("/jobs/register")
def register_jobs() -> dict[str, Any]:
    """Register all preconfigured jobs from JOB_MAP.

    This can be called on-demand or will also be invoked on server startup
    (frontend.startup_event already registers jobs).
    """
    created = []
    skipped = []

    for job_id, job_factory in JOB_MAP.items():
        if scheduler.get_job(job_id):
            skipped.append(job_id)
            continue
        try:
            job_factory()
            created.append(job_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"failed to register {job_id}: {e}")

    return {"created": created, "skipped": skipped}


@jobs.get("/status")
def scheduler_status():
    return {"running": scheduler.running}


@jobs.get("/runs")
def job_runs(job_id: str):
    """Return recent run history entries for a job (most recent first)."""
    runs = RUN_LOGS.get(job_id, [])
    # Return a shallow copy to avoid exposing internal lists
    return [{"ts": r.get("ts"), "status": r.get("status"), "detail": r.get("detail")} for r in runs]


@jobs.get("/ui", response_class=HTMLResponse)
def job_ui(request: Request):
    """Render the jobs dashboard template. Token must be provided as query param (enforced by router dependency)."""
    return templates.TemplateResponse("jobs.html", {"request": request})
