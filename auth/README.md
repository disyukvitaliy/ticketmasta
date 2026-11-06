# Auth

Run commands from the repository root.

```sh
./ape auth run <command>
```

## Migrations

- `./ape auth run goose create <name_of_migration> sql`
- `./ape auth run goose up`
- `./ape auth run goose down`

## Recreate the development database

This deletes all development Auth data.

```sh
docker compose up -d auth_db
docker compose exec auth_db dropdb -U auth --if-exists auth
docker compose exec auth_db createdb -U auth auth
./ape auth run goose up
```

## Recreate the test database

This deletes all test Auth data. Tests use a separate `auth_test` database.

```sh
docker compose up -d auth_db
docker compose exec auth_db dropdb -U auth --if-exists auth_test
docker compose exec auth_db createdb -U auth auth_test
docker compose --progress quiet -f docker-compose.yml -f test.docker-compose.yml run --rm auth goose up
```

## Tests

```sh
./ape auth test
```

## Decisions

### Unconfirmed account warning retries

Failed sends are logged without retries; retrying after partial delivery could
send duplicates. Setup errors still trigger Asynq retries.

The date window uses current UTC time, so retries after midnight can select
different users. We could attach an enqueue timestamp as scheduler metadata
(other tasks can ignore it), or save the first attempt's date in Redis.

We prefer to avoid a `warn_sent_at` column on `users` for a one-time notification.
Instead, Redis could track successful sends under `warn:<task_id>:<user_id>` so
retries skip them. Task IDs survive retries; the TTL must cover the retry window
and queue delays. Lost markers or a crash after sending can still cause duplicates.
If deletion requires a successful warning, consider a durable notification table.
These improvements are deferred.

### Kafka publishing

Publishing is currently not transactional with database writes. A user can be
created successfully without the corresponding event reaching `auth.users`,
leaving other services out of sync. Publish failures are logged, but failed events
are not saved for later delivery.

We need to consider the transactional outbox pattern so every committed user
creation is eventually reflected in Kafka. The user and an outgoing event would
be saved in the same database transaction, with a separate publisher retrying
delivery to Kafka.

### Confirmation email resend rate limiting

Auth limits confirmation email resends to one per normalized email address per
minute using an in-memory keyed rate limiter. Each Auth instance tracks its own
limits. If Auth runs multiple instances, use a distributed rate limiter so they
share the same limit.

The limiter is stored on `Server` so all requests share the same state. This is
simple with one limiter, but adding a separate field for every limited action
would clutter `Server`; group them under a limiter dependency if more are added.

## TODO

- Add an endpoint for retrieving current account details, including the account email.
- Let users delete all of their active sessions.
- Let users change their email address.
- Add password-reset emails so users can set a new password.
- Add an account/session list and let users log out other devices while keeping the current session.
