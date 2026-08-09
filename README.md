# TicketMasta

To run the app use `./ape up`

## Services

- [Auth](auth/README.md)
- [Core](core/README.md)

## TODO

1. Add a payment flow: payment-pending holds, provider idempotency, and webhook completion or failure.
2. Add hold cancellation.
3. Email tickets after purchase.
4. Support buying several ticket types in one purchase.
5. Add approximate ticket availability.
6. Add a billing service for profit tracking and invoicing.
7. Add a review and recommendation service.
8. Split `core/app.py` into modules.
9. Add tests.
10. Add Elasticsearch for events.
