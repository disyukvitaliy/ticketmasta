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

### Read replicas

We use replicas for reads that can tolerate a short delay, and the primary
database when a request needs the latest state to make a decision. For example,
venue and event catalogue reads can use a replica, while ticket holds and
purchase-related ticket-type reads use the primary database. A stale hold or
ticket quantity could otherwise lead to the wrong purchase decision.

### Log context

Logs include a request ID for work performed during an HTTP request and a job
ID for background jobs. This lets us find all log entries related to one
request or one job, even when several services or log lines are involved.

### Background jobs

We use Dramatiq with Redis for email notifications. It gives us workers and
retries without adding much infrastructure, which is a good fit for this
project. Not every email needs the same guarantee: non-critical notifications
can be best-effort. Ticket delivery is different: before it becomes the way a
customer receives a ticket, it should use a durable outbox or similar pattern
so the ticket is not lost between saving the purchase and queuing the job.

### Database scale

PostgreSQL is a performant starting point, but a single database is not assumed
to handle Ticketmaster-scale traffic. At that scale, we would need a
deliberate distributed data design, including regional distribution, rather
than trying to scale one primary database indefinitely.

## TODO

1. Add a payment flow: payment-pending holds, provider idempotency, and webhook completion or failure.
2. Support buying several ticket types in one purchase.
3. Add approximate ticket availability.
4. Add a billing service for profit tracking and invoicing.
5. Add a review and recommendation service.
6. Split `core/app.py` into modules.
7. Add tests.
8. Add Elasticsearch for events.
