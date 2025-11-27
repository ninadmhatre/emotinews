# Postgress DDL for status table
# id (auto increment), job_id (str), run_date(date), status(str), meta(json)

import datetime as dt

from sqlalchemy import String, Date, func, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Status(Base):
    __postgress_ddl__ = """
    CREATE TABLE IF NOT EXISTS status (
        id SERIAL PRIMARY KEY,
        job_id VARCHAR(128) NOT NULL,
        run_date DATE NOT NULL,
        hour_min VARCHAR(5) NOT NULL,
        status VARCHAR(12) NOT NULL,
        meta JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (job_id, run_date, hour_min)
    );
    """

    __sqlite_ddl__ = """
    CREATE TABLE IF NOT EXISTS status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id VARCHAR(128) NOT NULL,
        run_date DATE NOT NULL,
        hour_min VARCHAR(5) NOT NULL,
        status VARCHAR(12) NOT NULL,
        meta JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (job_id, run_date, hour_min)
    );
    """

    __tablename__ = "status"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(128))
    run_date: Mapped[dt.date] = mapped_column(Date)
    hour_min: Mapped[str] = mapped_column(String(5))
    status: Mapped[str] = mapped_column(String(12))
    meta = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Insert a unique constraint on job_id + run_date + hour_min
    UniqueConstraint("job_id", "run_date", "hour_min", name="uniq_job_id_hour_of_day")

    def __repr__(self):
        return f"Status(id={self.id!r}, job_id={self.job_id!r}, run_date={self.run_date!r}, hour_min={self.hour_min!r}, status={self.status!r}, meta={self.meta!r}, created_at={self.created_at!r}, updated_at={self.updated_at!r})"

    @property
    def postgress_ddl(self):
        return self.__postgress_ddl__

    @property
    def sqlite_ddl(self):
        return self.__sqlite_ddl__
