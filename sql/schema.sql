CREATE TABLE IF NOT EXISTS customer_support_tickets (
    id BIGSERIAL PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    created_date TIMESTAMP,
    issue_category TEXT NOT NULL DEFAULT 'Unknown',
    priority TEXT NOT NULL DEFAULT 'Unknown',
    first_response_minutes DOUBLE PRECISION,
    resolution_time_hours DOUBLE PRECISION,
    agent_experience_years DOUBLE PRECISION,
    reopened BOOLEAN,
    channel TEXT NOT NULL DEFAULT 'Unknown',
    customer_satisfaction DOUBLE PRECISION,
    source_hash TEXT NOT NULL UNIQUE,
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_support_tickets_issue_category
    ON customer_support_tickets (issue_category);

CREATE INDEX IF NOT EXISTS idx_customer_support_tickets_channel
    ON customer_support_tickets (channel);

CREATE INDEX IF NOT EXISTS idx_customer_support_tickets_priority
    ON customer_support_tickets (priority);

CREATE INDEX IF NOT EXISTS idx_customer_support_tickets_reopened
    ON customer_support_tickets (reopened);
