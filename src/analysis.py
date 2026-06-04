from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db import get_engine


PRIORITY_WEIGHT_SQL = """
CASE LOWER(COALESCE(priority::text, ''))
    WHEN 'low' THEN 1.0
    WHEN 'medium' THEN 2.0
    WHEN 'high' THEN 3.0
    WHEN 'urgent' THEN 4.0
    ELSE 1.0
END
"""

QUERIES = {
    "overview_kpis": """
        SELECT
            COUNT(*)::int AS total_tickets,
            ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours,
            ROUND(AVG(first_response_minutes)::numeric, 2) AS avg_first_response_minutes,
            ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
        FROM customer_support_tickets;
    """,
    "issue_category_counts": """
        SELECT issue_category, COUNT(*)::int AS ticket_count
        FROM customer_support_tickets
        GROUP BY issue_category
        ORDER BY ticket_count DESC;
    """,
    "channel_counts": """
        SELECT channel, COUNT(*)::int AS ticket_count
        FROM customer_support_tickets
        GROUP BY channel
        ORDER BY ticket_count DESC;
    """,
    "avg_resolution_by_issue_category": """
        SELECT
            issue_category,
            ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours
        FROM customer_support_tickets
        WHERE resolution_time_hours IS NOT NULL
        GROUP BY issue_category
        ORDER BY avg_resolution_time_hours DESC;
    """,
    "avg_resolution_by_priority": """
        SELECT
            priority,
            ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours
        FROM customer_support_tickets
        WHERE resolution_time_hours IS NOT NULL
        GROUP BY priority
        ORDER BY avg_resolution_time_hours DESC;
    """,
    "reopened_rate_overall": """
        SELECT ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
        FROM customer_support_tickets;
    """,
    "reopened_rate_by_issue_category": """
        SELECT
            issue_category,
            COUNT(*)::int AS ticket_count,
            ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
        FROM customer_support_tickets
        GROUP BY issue_category
        ORDER BY reopened_rate DESC NULLS LAST;
    """,
    "reopened_rate_by_channel": """
        SELECT
            channel,
            COUNT(*)::int AS ticket_count,
            ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
        FROM customer_support_tickets
        GROUP BY channel
        ORDER BY reopened_rate DESC NULLS LAST;
    """,
    "reopened_rate_by_priority": """
        SELECT
            priority,
            COUNT(*)::int AS ticket_count,
            ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
        FROM customer_support_tickets
        GROUP BY priority
        ORDER BY reopened_rate DESC NULLS LAST;
    """,
    "agent_experience_resolution": """
        SELECT
            agent_experience_years,
            COUNT(*)::int AS ticket_count,
            ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours
        FROM customer_support_tickets
        WHERE agent_experience_years IS NOT NULL
        GROUP BY agent_experience_years
        ORDER BY agent_experience_years;
    """,
    "agent_experience_reopened": """
        SELECT
            agent_experience_years,
            COUNT(*)::int AS ticket_count,
            ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
        FROM customer_support_tickets
        WHERE agent_experience_years IS NOT NULL
        GROUP BY agent_experience_years
        ORDER BY agent_experience_years;
    """,
    "risk_ranking": f"""
        WITH base AS (
            SELECT
                issue_category,
                COUNT(*)::int AS ticket_count,
                AVG(reopened::int) AS reopened_rate_raw,
                AVG(resolution_time_hours) AS avg_resolution_time_hours,
                AVG({PRIORITY_WEIGHT_SQL}) AS avg_priority_weight
            FROM customer_support_tickets
            GROUP BY issue_category
        ),
        bounds AS (
            SELECT
                MIN(reopened_rate_raw) AS min_reopened_rate,
                MAX(reopened_rate_raw) AS max_reopened_rate,
                MIN(avg_resolution_time_hours) AS min_resolution_time,
                MAX(avg_resolution_time_hours) AS max_resolution_time,
                MIN(avg_priority_weight) AS min_priority_weight,
                MAX(avg_priority_weight) AS max_priority_weight
            FROM base
        ),
        scored AS (
            SELECT
                base.issue_category,
                base.ticket_count,
                ROUND((base.reopened_rate_raw * 100)::numeric, 2) AS reopened_rate,
                ROUND(base.avg_resolution_time_hours::numeric, 2) AS avg_resolution_time_hours,
                ROUND(base.avg_priority_weight::numeric, 2) AS avg_priority_weight,
                COALESCE(
                    (base.reopened_rate_raw - bounds.min_reopened_rate)
                    / NULLIF(bounds.max_reopened_rate - bounds.min_reopened_rate, 0),
                    0
                ) AS normalized_reopened_rate,
                COALESCE(
                    (base.avg_resolution_time_hours - bounds.min_resolution_time)
                    / NULLIF(bounds.max_resolution_time - bounds.min_resolution_time, 0),
                    0
                ) AS normalized_resolution_time,
                COALESCE(
                    (base.avg_priority_weight - bounds.min_priority_weight)
                    / NULLIF(bounds.max_priority_weight - bounds.min_priority_weight, 0),
                    0
                ) AS normalized_priority_weight
            FROM base
            CROSS JOIN bounds
        )
        SELECT
            issue_category,
            ticket_count,
            reopened_rate,
            avg_resolution_time_hours,
            avg_priority_weight,
            ROUND(normalized_reopened_rate::numeric, 4) AS normalized_reopened_rate,
            ROUND(normalized_resolution_time::numeric, 4) AS normalized_resolution_time,
            ROUND(normalized_priority_weight::numeric, 4) AS normalized_priority_weight,
            ROUND((
                0.5 * normalized_reopened_rate
                + 0.3 * normalized_resolution_time
                + 0.2 * normalized_priority_weight
            )::numeric, 4) AS risk_score
        FROM scored
        ORDER BY risk_score DESC, ticket_count DESC
        LIMIT 5;
    """,
    "recommendation_kpis": f"""
        WITH base AS (
            SELECT
                issue_category,
                COUNT(*)::int AS ticket_count,
                AVG(reopened::int) AS reopened_rate_raw,
                AVG(resolution_time_hours) AS avg_resolution_time_hours,
                AVG({PRIORITY_WEIGHT_SQL}) AS avg_priority_weight
            FROM customer_support_tickets
            GROUP BY issue_category
        ),
        overall AS (
            SELECT
                COUNT(*) AS total_tickets,
                AVG(reopened::int) AS overall_reopened_rate_raw,
                AVG(resolution_time_hours) AS overall_resolution_time_hours
            FROM customer_support_tickets
        ),
        ranked AS (
            SELECT
                base.*,
                RANK() OVER (ORDER BY avg_priority_weight DESC) AS priority_weight_rank,
                COUNT(*) OVER () AS category_count
            FROM base
        )
        SELECT
            ranked.issue_category,
            ranked.ticket_count,
            ROUND((ranked.reopened_rate_raw * 100)::numeric, 2) AS reopened_rate,
            ROUND((overall.overall_reopened_rate_raw * 100)::numeric, 2)
                AS overall_reopened_rate,
            ROUND(
                ((ranked.reopened_rate_raw - overall.overall_reopened_rate_raw) * 100)::numeric,
                2
            ) AS reopened_rate_delta,
            ROUND(ranked.avg_resolution_time_hours::numeric, 2) AS avg_resolution_time_hours,
            ROUND(overall.overall_resolution_time_hours::numeric, 2)
                AS overall_resolution_time_hours,
            ROUND(
                (ranked.avg_resolution_time_hours - overall.overall_resolution_time_hours)::numeric,
                2
            ) AS resolution_time_delta,
            ROUND(((ranked.ticket_count::numeric / overall.total_tickets) * 100), 2)
                AS category_share,
            ROUND(ranked.avg_priority_weight::numeric, 2) AS avg_priority_weight,
            ranked.priority_weight_rank::int,
            ranked.category_count::int
        FROM ranked
        CROSS JOIN overall
        ORDER BY ranked.issue_category;
    """,
}


def run_query(query_name: str) -> pd.DataFrame:
    if query_name not in QUERIES:
        raise KeyError(f"Unknown query name: {query_name}")

    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql_query(text(QUERIES[query_name]), conn)


def run_all_queries() -> dict[str, pd.DataFrame]:
    return {name: run_query(name) for name in QUERIES}


def run_ai_context_queries() -> dict[str, pd.DataFrame]:
    query_names = [
        "overview_kpis",
        "issue_category_counts",
        "channel_counts",
        "avg_resolution_by_issue_category",
        "avg_resolution_by_priority",
        "reopened_rate_by_issue_category",
        "reopened_rate_by_channel",
        "reopened_rate_by_priority",
        "agent_experience_resolution",
        "agent_experience_reopened",
        "risk_ranking",
    ]
    return {name: run_query(name) for name in query_names}


def build_analysis_summary(results: dict[str, pd.DataFrame]) -> str:
    lines = []
    for name, df in results.items():
        lines.append(f"[{name}]")
        if df.empty:
            lines.append("No rows")
        else:
            lines.append(df.head(10).to_string(index=False))
        lines.append("")
    return "\n".join(lines)
