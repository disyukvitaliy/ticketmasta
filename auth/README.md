# Auth

Run commands from the repository root.

```sh
./ape auth run
```

## Migrations

- `goose create <name_of_migration> sql`
- `goose up`
- `goose down`

## Tests

Tests use a separate `auth_test` database.

```sh
docker compose exec auth_db dropdb -U auth --if-exists auth_test
docker compose exec auth_db createdb -U auth auth_test
./ape auth run goose up
./ape auth test
```
