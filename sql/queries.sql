-- 1. Operational Overview KPI
SELECT
    COUNT(*)::int AS total_tickets,
    ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours,
    ROUND(AVG(first_response_minutes)::numeric, 2) AS avg_first_response_minutes,
    ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
FROM customer_support_tickets;

-- 2. Issue Category 분포
SELECT issue_category, COUNT(*)::int AS ticket_count
FROM customer_support_tickets
GROUP BY issue_category
ORDER BY ticket_count DESC;

-- 3. Channel 분포
SELECT channel, COUNT(*)::int AS ticket_count
FROM customer_support_tickets
GROUP BY channel
ORDER BY ticket_count DESC;

-- 4. Issue Category별 평균 처리시간
SELECT
    issue_category,
    ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours
FROM customer_support_tickets
WHERE resolution_time_hours IS NOT NULL
GROUP BY issue_category
ORDER BY avg_resolution_time_hours DESC;

-- 5. Priority별 평균 처리시간
SELECT
    priority,
    ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours
FROM customer_support_tickets
WHERE resolution_time_hours IS NOT NULL
GROUP BY priority
ORDER BY avg_resolution_time_hours DESC;

-- 6. 전체 Reopened Rate
SELECT ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
FROM customer_support_tickets;

-- 7. Issue Category별 Reopened Rate
SELECT
    issue_category,
    COUNT(*)::int AS ticket_count,
    ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
FROM customer_support_tickets
GROUP BY issue_category
ORDER BY reopened_rate DESC NULLS LAST;

-- 8. Channel별 Reopened Rate
SELECT
    channel,
    COUNT(*)::int AS ticket_count,
    ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
FROM customer_support_tickets
GROUP BY channel
ORDER BY reopened_rate DESC NULLS LAST;

-- 9. Priority별 Reopened Rate
SELECT
    priority,
    COUNT(*)::int AS ticket_count,
    ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
FROM customer_support_tickets
GROUP BY priority
ORDER BY reopened_rate DESC NULLS LAST;

-- 10. Agent Experience vs Resolution Time
SELECT
    agent_experience_years,
    COUNT(*)::int AS ticket_count,
    ROUND(AVG(resolution_time_hours)::numeric, 2) AS avg_resolution_time_hours
FROM customer_support_tickets
WHERE agent_experience_years IS NOT NULL
GROUP BY agent_experience_years
ORDER BY agent_experience_years;

-- 11. Agent Experience vs Reopened Rate
SELECT
    agent_experience_years,
    COUNT(*)::int AS ticket_count,
    ROUND((AVG(reopened::int) * 100)::numeric, 2) AS reopened_rate
FROM customer_support_tickets
WHERE agent_experience_years IS NOT NULL
GROUP BY agent_experience_years
ORDER BY agent_experience_years;
