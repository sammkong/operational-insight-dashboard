import argparse
from dataclasses import dataclass
from typing import Any

import pandas as pd
from sqlalchemy import text

from src.db import create_schema, get_engine


LOAD_COLUMNS = [
    "ticket_id",
    "created_date",
    "issue_category",
    "priority",
    "first_response_minutes",
    "resolution_time_hours",
    "agent_experience_years",
    "reopened",
    "channel",
    "customer_satisfaction",
    "source_hash",
]
DATETIME_COLUMNS = ["created_date"]
NUMERIC_COLUMNS = [
    "first_response_minutes",
    "resolution_time_hours",
    "agent_experience_years",
    "customer_satisfaction",
]
TEXT_COLUMNS = ["ticket_id", "issue_category", "priority", "channel", "source_hash"]


@dataclass
class LoadResult:
    inserted_count: int
    skipped_count: int
    failed_count: int
    error_examples: list[str]


def normalize_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        return value.item()
    return value


def parse_bool(value: Any) -> bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "t", "yes", "y", "1", "reopened"}:
        return True
    if normalized in {"false", "f", "no", "n", "0", "not reopened", "closed", "resolved"}:
        return False
    return None


def prepare_dataframe(csv_path: str) -> pd.DataFrame:
    dtype_map = {col: "string" for col in TEXT_COLUMNS}
    df = pd.read_csv(csv_path, dtype=dtype_map)

    missing_columns = [col for col in LOAD_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {missing_columns}")

    df = df[LOAD_COLUMNS].copy()
    for col in DATETIME_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["reopened"] = df["reopened"].map(parse_bool).astype("boolean")
    return df


def row_to_params(row: pd.Series) -> dict[str, Any]:
    return {col: normalize_value(row[col]) for col in LOAD_COLUMNS}


def load_processed_csv(csv_path: str) -> LoadResult:
    engine = get_engine()
    create_schema(engine)
    df = prepare_dataframe(csv_path)

    insert_sql = text(
        """
        INSERT INTO customer_support_tickets (
            ticket_id,
            created_date,
            issue_category,
            priority,
            first_response_minutes,
            resolution_time_hours,
            agent_experience_years,
            reopened,
            channel,
            customer_satisfaction,
            source_hash
        )
        VALUES (
            :ticket_id,
            :created_date,
            :issue_category,
            :priority,
            :first_response_minutes,
            :resolution_time_hours,
            :agent_experience_years,
            :reopened,
            :channel,
            :customer_satisfaction,
            :source_hash
        )
        ON CONFLICT (source_hash) DO NOTHING
        """
    )

    inserted_count = 0
    skipped_count = 0
    failed_count = 0
    error_examples: list[str] = []

    with engine.connect() as conn:
        for idx, row in df.iterrows():
            params = row_to_params(row)
            transaction = conn.begin()
            try:
                result = conn.execute(insert_sql, params)
                transaction.commit()
                if result.rowcount == 1:
                    inserted_count += 1
                else:
                    skipped_count += 1
            except Exception as exc:
                transaction.rollback()
                failed_count += 1
                if len(error_examples) < 5:
                    ticket_id = params.get("ticket_id")
                    error_examples.append(f"row={idx}, ticket_id={ticket_id}, error={exc}")

    return LoadResult(
        inserted_count=inserted_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        error_examples=error_examples,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Load processed ticket CSV into PostgreSQL.")
    parser.add_argument("--csv", required=True, help="Path to processed CSV file.")
    args = parser.parse_args()

    result = load_processed_csv(args.csv)
    print(f"inserted_count={result.inserted_count:,}")
    print(f"skipped_count={result.skipped_count:,}")
    print(f"failed_count={result.failed_count:,}")
    if result.error_examples:
        print("error_examples:")
        for error in result.error_examples:
            print(f"- {error}")


if __name__ == "__main__":
    main()
