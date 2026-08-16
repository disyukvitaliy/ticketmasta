# TicketMasta

To run the app use `./ape up`

## Services

- [Auth](auth/README.md)
- [Core](core/README.md)

## Decisions

### Ticket holds and inventory locking

Creating a ticket hold locks its ticket type with `SELECT ... FOR UPDATE`, then
checks and reduces the available quantity in the same transaction. This prevents
two concurrent requests from reserving the same tickets.

A single conditional `UPDATE` could do the check and reduction in one query: `UPDATE ticket_types SET quantity = quantity - :quantity WHERE id = :ticket_type_id AND quantity >= :quantity RETURNING id`.
We use the lock-and-check flow for now because it keeps the outcomes clear: a
missing ticket type and insufficient availability can have different responses.

## TODO

1. Add a payment flow: payment-pending holds, provider idempotency, and webhook completion or failure.
2. Support buying several ticket types in one purchase.
3. Add approximate ticket availability.
4. Add a billing service for profit tracking and invoicing.
5. Add a review and recommendation service.
6. Split `core/app.py` into modules.
7. Add tests.
8. Add Elasticsearch for events.
