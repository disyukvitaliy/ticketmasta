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

## Background jobs

`core_worker` consumes Redis-backed jobs. Completing a ticket hold enqueues an
email task, which the worker sends through Mailpit. Open Mailpit at
http://localhost:8025.
