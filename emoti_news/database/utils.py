from typing import Any, Self
import json
from pathlib import Path
from enum import StrEnum

from sqlalchemy import Engine, create_engine

from emoti_news.config.database import DB_TYPE, POSTGRES, SQLITE
from emoti_news.config import PROJECT_ROOT

__all__ = ["DBInstance", "DB", "DBType"]


class DBType(StrEnum):
    Postgress = "POSTGRESS"
    Sqlite = "SQLITE"


class DBInstance:
    def __init__(self, db_type: str | DBType):
        self.db_type = db_type
        self._engine = None

    def _json_serializer(self, value: dict[str, Any]) -> str:
        return json.dumps(value, indent=4, default=str)

    def _json_deserializer(self, value: str) -> dict[str, Any]:
        return json.loads(value)

    def get_db_cfg(self) -> dict[str, Any]:
        if self.db_type == DBType.Postgress:
            return POSTGRES

        return {"path": SQLITE["path"]}

    def _get_postgres_url(self) -> str:
        cfg = self.get_db_cfg()
        return f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"

    def _get_sqlite_url(self) -> str:
        cfg = self.get_db_cfg()
        db_path = cfg["path"]

        if not Path(db_path).is_absolute():
            db_path = PROJECT_ROOT.joinpath(db_path)

        return f"sqlite:///{db_path}"

    def get_engine(self) -> Engine:
        """Get database engine based on configuration."""
        if self._engine is not None:
            return self._engine

        if self.db_type == DBType.Postgress:
            self._engine = create_engine(
                self._get_postgres_url(),
                json_serializer=self._json_serializer,
                json_deserializer=self._json_deserializer,
                isolation_level="AUTOCOMMIT",
            )
        else:  # sqlite
            self._engine = create_engine(
                self._get_sqlite_url(),
                json_serializer=self._json_serializer,
                json_deserializer=self._json_deserializer,
                connect_args={"check_same_thread": False},
            )

        return self._engine

    def clear_engine(self) -> Self:
        if self._engine:
            self._engine = None

        return self


# Global instance
DB = DBInstance(DB_TYPE)
