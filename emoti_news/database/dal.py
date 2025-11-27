import datetime as dt
from typing import Any

import sqlalchemy
from sqlalchemy import insert, update
from sqlalchemy.exc import IntegrityError

from emoti_news.database import Status, DB, News, Base
from emoti_news.dtypes import JobStatus, Article
from emoti_news.loggers import backend_logger as log


def add_new_status(values: dict):
    with DB.get_engine().connect() as conn:
        conn.execute(insert(Status).values(values))
        conn.commit()


def update_status(
    job_id: str,
    run_date: dt.date,
    hour_min: str,
    meta: dict,
    job_status: JobStatus | str,
):
    status = job_status.value if isinstance(job_status, JobStatus) else job_status

    with DB.get_engine().connect() as conn:
        stmt = (
            update(Status)
            .where(
                (Status.job_id == job_id)
                & (Status.run_date == run_date)
                & (Status.hour_min == hour_min)
            )
            .values(status=status.upper(), meta=meta)
        )
        conn.execute(stmt)
        conn.commit()


def insert_article(articles: list[Article]):
    with DB.get_engine().connect() as conn:
        with conn.begin():
            for article in articles:
                log.info(f"Inserting article: {article.uid}")

                try:
                    values = article.as_dict(skip_keys=["desc", "content"])
                    conn.execute(insert(News).values(values))
                except IntegrityError as e:
                    # Is it Unique or Not Null failed?
                    if "UNIQUE constraint failed" in str(e):
                        failure_reason = "Already exists"
                    elif "NOT NULL constraint failed" in str(e):
                        failure_reason = "Missing required fields"
                    else:
                        failure_reason = "Unknown"

                    log.warning(
                        f"Failed: {failure_reason}: {article.uid}, skipping [{article}] exception: {e}"
                    )
                except Exception as e:
                    log.error(f"Error inserting articles: {e}")
                    conn.rollback()


def create_all_tables():
    Base.metadata.create_all(DB.get_engine())
