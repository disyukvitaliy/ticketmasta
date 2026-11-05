# Core

Run commands from the repository root.

```sh
./ape core run
./ape core bash
```

## Linting

```sh
./ape core lint
./ape core lint --fix
./ape core format
./ape core imports
```

## Tests

Tests use a separate `core_test` database.

```sh
docker compose exec core_db dropdb -U core --if-exists core_test
docker compose exec core_db createdb -U core core_test
docker compose --progress quiet -f docker-compose.yml -f test.docker-compose.yml run --rm core alembic upgrade head
./ape core test
```

## Migrations

Create a migration:

```sh
./ape core run alembic revision -m "create venues"
```

Apply migrations:

```sh
./ape core run alembic upgrade head
```

Roll back the last migration:

```sh
./ape core run alembic downgrade -1
```

## Seeds

Reset and seed the core database:

```sh
./ape core run python seeds.py
```

## Flask shell

Start a shell with the application loaded:

```sh
./ape core sh
```

## Decisions

### Worker

We use Dramatiq with Redis for background jobs such as ticket emails and hold
expiration. It provides task queues, retries, and configurable process and thread
counts while keeping handlers synchronous.

### Consumer

We chose FastStream with its aiokafka backend to run multiple processes, each
using threads for efficient concurrent partition processing. Synchronous handlers
can overlap database I/O while preserving order within each partition. Topics can
be deployed independently with different process counts and concurrency settings.
Messages are handled individually for now; batch processing is available for
future efficiency improvements.

Message schema validation, custom error handling, retry limits and backoff, and
dead-letter queues (DLQs) are deferred. For now, failed messages are retried through
FastStream's `NACK_ON_ERROR` policy.

### Profile creation

Core creates profiles asynchronously on user creation, before confirmation gives
the user access to the system. This provides a window to prepare the profile,
but does not guarantee it will be ready in time. A user may briefly exist
without a profile while the creation event is waiting to be processed. We need
monitoring to detect these gaps, distinguish normal delays from missing events
or processing failures, and trigger recovery when needed.

## TODO

- Add a payment flow: payment-pending holds, provider idempotency, and webhook
  completion or failure.
- Support buying several ticket types in one purchase.
- Add approximate ticket availability.
- Add Elasticsearch for events.
- Manage and lock Python dependencies with `pyproject.toml` and a modern dependency tool.
