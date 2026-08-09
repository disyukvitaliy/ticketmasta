# Core

Run commands from the repository root.

```sh
./ape core run
./ape core bash
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
