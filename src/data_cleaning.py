import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd


STANDARD_COLUMNS = {
    "ticket_id": ["ticket_id", "ticket id", "id", "ticket number"],
    "created_date": ["created_date", "created date", "created_at", "created at", "date"],
    "issue_category": ["issue_category", "issue category", "category", "issue type", "ticket type"],
    "priority": ["priority", "ticket priority", "urgency"],
    "first_response_minutes": [
        "first_response_minutes",
        "first response minutes",
        "first response time",
        "first_response_time",
    ],
    "resolution_time_hours": [
        "resolution_time_hours",
        "resolution time hours",
        "resolution_time",
        "resolution time",
        "time to resolution",
    ],
    "agent_experience_years": [
        "agent_experience_years",
        "agent experience years",
        "agent experience",
        "experience years",
    ],
    "reopened": ["reopened", "reopen", "reopened status", "is reopened"],
    "channel": ["channel", "ticket channel", "contact channel", "source"],
    "customer_satisfaction": [
        "customer_satisfaction",
        "customer satisfaction",
        "customer satisfaction rating",
        "satisfaction score",
        "satisfaction",
        "csat",
    ],
}

LOAD_COLUMNS = list(STANDARD_COLUMNS.keys())
TEXT_DEFAULTS = {
    "issue_category": "Unknown",
    "priority": "Unknown",
    "channel": "Unknown",
}
NUMERIC_COLUMNS = [
    "first_response_minutes",
    "resolution_time_hours",
    "agent_experience_years",
    "customer_satisfaction",
]


def normalize_column_name(name: str) -> str:
    cleaned = str(name).strip().lower()
    cleaned = re.sub(r"[\W]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def find_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized = {normalize_column_name(col): col for col in columns}
    for candidate in candidates:
        match = normalized.get(normalize_column_name(candidate))
        if match:
            return match

    for normalized_col, original_col in normalized.items():
        if any(normalize_column_name(candidate) in normalized_col for candidate in candidates):
            return original_col
    return None


def parse_numeric(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.extract(r"([-+]?\d*\.?\d+)")[0]
    return pd.to_numeric(cleaned, errors="coerce")


def parse_reopened(value: object) -> bool | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 1:
            return True
        if value == 0:
            return False

    normalized = normalize_column_name(value)
    true_values = {"true", "t", "yes", "y", "1", "reopened", "re open", "opened again"}
    false_values = {
        "false",
        "f",
        "no",
        "n",
        "0",
        "not reopened",
        "not re opened",
        "closed",
        "resolved",
    }
    if normalized in true_values:
        return True
    if normalized in false_values:
        return False
    return None


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    for standard_name, candidates in STANDARD_COLUMNS.items():
        source_col = find_column(list(df.columns), candidates)
        result[standard_name] = df[source_col] if source_col else pd.NA

    for col, default in TEXT_DEFAULTS.items():
        result[col] = result[col].fillna(default).astype(str).str.strip()
        result[col] = result[col].replace({"": default, "nan": default, "None": default})

    return result


def add_source_hash(df: pd.DataFrame) -> pd.DataFrame:
    hash_input = df.fillna("").astype(str).agg("|".join, axis=1)
    df["source_hash"] = hash_input.map(lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest())
    return df


def clean_customer_support_data(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    input_path = Path(input_path)
    output_path = Path(output_path)
    df = pd.read_csv(input_path)

    cleaned = standardize_columns(df)
    cleaned["created_date"] = pd.to_datetime(cleaned["created_date"], errors="coerce")

    for col in NUMERIC_COLUMNS:
        cleaned[col] = parse_numeric(cleaned[col])

    cleaned["reopened"] = cleaned["reopened"].map(parse_reopened).astype("boolean")

    cleaned["ticket_id"] = cleaned["ticket_id"].fillna("").astype(str).str.strip()
    missing_ticket_id = cleaned["ticket_id"].isin(["", "nan", "None"])
    cleaned.loc[missing_ticket_id, "ticket_id"] = [
        f"generated-{idx}" for idx in cleaned.index[missing_ticket_id]
    ]

    cleaned = add_source_hash(cleaned)
    cleaned = cleaned.drop_duplicates(subset=["source_hash"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output_path, index=False)
    return cleaned


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean customer support ticket CSV data.")
    parser.add_argument("--input", required=True, help="Path to raw CSV file.")
    parser.add_argument("--output", required=True, help="Path to processed CSV file.")
    args = parser.parse_args()

    cleaned = clean_customer_support_data(args.input, args.output)
    print(f"Saved {len(cleaned):,} rows to {args.output}")


if __name__ == "__main__":
    main()
