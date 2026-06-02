from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import DATABASE_URL, SQL_DIR


def get_engine() -> Engine:
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def execute_sql_file(sql_path: str | Path, engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    sql = Path(sql_path).read_text(encoding="utf-8")
    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def create_schema(engine: Engine | None = None) -> None:
    execute_sql_file(SQL_DIR / "schema.sql", engine=engine)
