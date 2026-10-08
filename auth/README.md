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

## TODO

- Complete the email-confirmation flow: receive a confirmation token and persist that the user's email has been confirmed.
- Let users delete all of their active sessions.
- Let users change their email address.
- Add password-reset emails so users can set a new password.
- Add an account/session list and let users log out other devices while keeping the current session.
- Publish a user-signup event to Kafka.
