# TicketMasta

To run the app use `./ape up`

## Services

- [Auth](auth/README.md)
- [Core](core/README.md)

## TODO

1. Add a payment flow: payment-pending holds, provider idempotency, and webhook completion or failure.
2. Add hold cancellation.
3. Support buying several ticket types in one purchase.
4. Add approximate ticket availability.
5. Add a billing service for profit tracking and invoicing.
6. Add a review and recommendation service.
7. Split `core/app.py` into modules.
8. Add tests.
9. Add Elasticsearch for events.
