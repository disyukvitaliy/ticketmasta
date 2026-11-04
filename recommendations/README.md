# Recommendations

Planned service for saving events, collecting reviews and ratings, and suggesting
upcoming events based on users' interests. Core continues to own event details,
availability, and ticket purchases.

## Storage and messaging

- **PostgreSQL** — stores saves, reviews, ratings, similar-user matches, and
  prepared recommendations. It handles transactional operations and fast API
  reads without running large analytical queries for each request.
- **Kafka** — carries events published directly by applications when users save,
  unsave, or review events, alongside relevant activity from other services.
- **ClickHouse** — the analytics platform ingests these events through its Kafka
  integration. Background jobs use the analytical data to calculate similarities
  and recommendation scores with SQL, without training machine learning models.

## Data flow

```text
User actions → Recommendations → PostgreSQL
                      │
                Published events
                      ↓
Other services → Kafka → ClickHouse
                             │
                  Recommendations background jobs
                             ↓
                        PostgreSQL → Recommendations API
```

## Recommendation approach

Background jobs periodically analyze user interests and activity in ClickHouse
to find similarities and generate recommendations. Results are stored in
PostgreSQL for the API to serve without repeating the analysis on each request.
The exact algorithms will be decided during implementation.

## Local development

The service, PostgreSQL, Kafka, and ClickHouse can run locally in Docker Compose.
This folder will own the API, transactional schemas, and background SQL jobs;
the analytics platform owns ClickHouse ingestion and analytical schemas.

This README describes the intended architecture; implementation is not added yet.
