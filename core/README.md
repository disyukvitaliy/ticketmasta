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

## Background jobs

`core_worker` consumes Redis-backed jobs. Completing a ticket hold enqueues an
email task, which the worker sends through Mailpit. Open Mailpit at
http://localhost:8025.

## TODO

1. Add a payment flow: payment-pending holds, provider idempotency, and webhook
   completion or failure.
2. Support buying several ticket types in one purchase.
3. Add approximate ticket availability.
4. Add tests.
5. Add Elasticsearch for events.
6. Have `send_ticket_email` query its ticket type and event data itself.
