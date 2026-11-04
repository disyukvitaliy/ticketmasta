# Analytics

Planned analytical data platform that collects events from other services,
stores them in an OLAP database, and makes them available for dashboards and
ad hoc SQL analysis.

## Stack

- **ClickHouse** — a column-oriented OLAP database suited to storing historical
  events and running analytical queries. It supports SQL, runs locally, and can
  consume Kafka messages without a custom consumer application.
- **Kafka** — transports events published directly by applications, rather than
  streaming database changes through CDC. Ingestion happens asynchronously.
- **Grafana** — connects directly to ClickHouse to build charts, tables, and
  dashboards through its ClickHouse plugin, using a visual query builder or SQL.
  It also supports monitoring through separate data sources such as Prometheus,
  allowing one visualization tool for both business and operational dashboards.

## Data flow

```text
Auth / Core → Kafka → ClickHouse → Grafana
```

Applications publish events to Kafka. We define the message structures and
analytical schemas, then configure ClickHouse's built-in Kafka integration:

1. A **Kafka-engine table** defines the broker, topic, consumer group, message
   format, and incoming fields.
2. A **materialized view** maps and transforms incoming records.
3. A persistent **MergeTree-family table** stores the results for querying.

This avoids writing a custom consumer or reporting API initially. This folder
will own ingestion configuration, analytical schemas, and SQL transformations;
it does not initially need a standalone application process.

## Local development

The entire stack can run locally in Docker Compose with one Kafka broker, one
ClickHouse instance, and Grafana. Persistent volumes will retain data and
dashboards. No cloud services are required.

This README describes the intended architecture; runtime configuration is not
implemented yet.
