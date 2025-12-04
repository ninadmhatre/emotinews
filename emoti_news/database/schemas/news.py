# Postgress DDL for status table
# id (auto increment), job_id (str), run_date(date), status(str), meta(json)

import datetime as dt

from sqlalchemy import String, Date, func, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class News(Base):
    __postgress_ddl__ = """
    CREATE TABLE IF NOT EXISTS news (
        id SERIAL PRIMARY KEY,
        uid VARCHAR(64) NOT NULL,
        country VARCHAR(12) NOT NULL,
        category VARCHAR(32) NOT NULL,
        source VARCHAR(32) NOT NULL,
        url VARCHAR(256) NOT NULL,
        title VARCHAR(256) NOT NULL,
        description TEXT NOT NULL,
        sentiment VARCHAR(12) NOT NULL DEFAULT '<UNCHECKED>',
        sentiment_score FLOAT DEFAULT 0,
        clickbait BOOLEAN DEFAULT FALSE,
        news_api VARCHAR(12),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (uid)
    );
    
    CREATE INDEX cou_cat on news (country, category);
    CREATE INDEX src_cat on news (source, category);
    CREATE INDEX src on news (source);
    """

    __sqlite_ddl__ = """
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT NOT NULL,
        country TEXT NOT NULL,
        category TEXT NOT NULL,
        source TEXT NOT NULL,
        url TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        sentiment TEXT NOT NULL DEFAULT '<UNCHECKED>',
        sentiment_score REAL DEFAULT 0,
        clickbait INTEGER DEFAULT 0, -- boolean stored as 0/1
        news_api TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (uid)
    );
    """

    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(64))
    country: Mapped[str] = mapped_column(String(12))
    category: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32))
    url: Mapped[str] = mapped_column(String(256))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(String)
    sentiment: Mapped[str] = mapped_column(String(12), default="<UNCHECKED>")
    sentiment_score: Mapped[float] = mapped_column(default=0)
    clickbait: Mapped[bool] = mapped_column(default=False)
    news_api: Mapped[str] = mapped_column(String(12))
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    UniqueConstraint(uid)

    def __repr__(self):
        return (
            f"News(id={self.id!r}, uid={self.uid!r}, country={self.country!r}, category={self.category!r}, "
            f"source={self.source!r}, url={self.url!r}, title={self.title!r}, sentiment={self.sentiment!r}, "
            f"sentiment_score={self.sentiment_score!r}, clickbait={self.clickbait!r})"
        )

    @property
    def postgress_ddl(self):
        return self.__postgress_ddl__

    @property
    def sqlite_ddl(self):
        return self.__sqlite_ddl__
