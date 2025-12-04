from enum import StrEnum
from typing import Annotated, Literal

from fastapi import Depends, APIRouter, HTTPException

from emoti_news.frontend.apis import has_token
from emoti_news.jobs import scheduler, JOB_MAP
from emoti_news.loggers import backend_logger as log


class _Status(StrEnum):
    Started = "Started"
    AlreadyRunning = "AlreadyRunning"
    Stopped = "Stopped"
    Running = "Running"
    NotRunning = "NotRunning"


sched = APIRouter(prefix="/sched", tags=["Scheduler"], dependencies=[Depends(has_token)])


@sched.get("/admin", summary="Check scheduler status")
async def admin_sched(action: Literal["start", "shutdown", "status"]):
    if action == "start":
        if scheduler.running:
            _status = _Status.AlreadyRunning
        else:
            log.debug("Starting scheduler")
            scheduler.start()
            _status = _Status.Started
    elif action == "stop":
        if scheduler.running:
            log.debug("Stopping scheduler")
            scheduler.shutdown(wait=False)
            _status = _Status.Stopped
        else:
            _status = _Status.NotRunning
    else:
        _status = _Status.Running if scheduler.running else _Status.NotRunning

    return {"status": _status}
