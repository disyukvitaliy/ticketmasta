# TicketMasta

To run the app use `./ape up`

## Auth app
Run the auth app:

```sh
./ape auth run
```

### Migrations
- goose create <name_of_migration> sql
- goose up
- goose down

### Tests
Auth tests should use a separate database named `auth_test` on the same Postgres server.

Drop and recreate the test database:

```sh
docker compose exec auth_db dropdb -U auth --if-exists auth_test
docker compose exec auth_db createdb -U auth auth_test
```

Run auth migrations against the test database:

```sh
./ape auth run goose up
```

Run auth tests against the test database:

```sh
./ape auth test
```
