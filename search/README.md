# Search

Planned service for finding events through text search, filters, and sorting.
`events` is another possible name. Core remains the source of truth for event
details, ticket availability, and purchases.

## Architecture

- **Elasticsearch** stores a searchable projection of the event catalog.
- **Kafka indexing worker** consumes application-published events and updates
  search documents.
- **Search API** accepts queries and returns matching event summaries.
- **Reindexing job** populates or rebuilds the index from Core's catalog.

```text
Core → Kafka → Indexing worker → Elasticsearch ← Search API ← Web
```

Keeping search separate allows indexing and discovery traffic to scale and
evolve independently from Core. Search results may lag behind catalog updates;
Core checks current availability when purchasing.

The service can run locally with Kafka and Elasticsearch in Docker Compose.
This README describes the intended architecture; implementation is not added yet.
