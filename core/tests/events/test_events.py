from datetime import datetime, timedelta

from tests.factories import EventFactory, VenueFactory


def test_list_events_returns_upcoming_events_by_start_time(client):
    venue = VenueFactory(name="Alpha Arena")
    later_event = EventFactory(
        venue_id=venue.id,
        name="Later Event",
        starts_at=datetime.now() + timedelta(days=2),
    )
    earlier_event = EventFactory(
        venue_id=venue.id,
        name="Earlier Event",
        starts_at=datetime.now() + timedelta(days=1),
    )

    response = client.get("/events")

    assert response.status_code == 200
    assert response.json == [
        {
            "id": earlier_event.id,
            "name": "Earlier Event",
            "venue": {"id": venue.id, "name": "Alpha Arena"},
        },
        {
            "id": later_event.id,
            "name": "Later Event",
            "venue": {"id": venue.id, "name": "Alpha Arena"},
        },
    ]


def test_list_events_for_venue_returns_its_events(client):
    venue = VenueFactory(name="Alpha Arena")
    event = EventFactory(
        venue_id=venue.id,
        name="Concert",
    )
    other_venue = VenueFactory(name="Beta Hall")
    EventFactory(venue_id=other_venue.id)

    response = client.get(f"/venues/{venue.id}/events")

    assert response.status_code == 200
    assert response.json == [
        {
            "id": event.id,
            "name": "Concert",
            "venue": {"id": venue.id, "name": "Alpha Arena"},
        }
    ]


def test_get_event_returns_event(client):
    venue = VenueFactory()
    event = EventFactory(venue_id=venue.id, name="Concert")

    response = client.get(f"/events/{event.id}")

    assert response.status_code == 200
    assert response.json == {
        "id": event.id,
        "name": "Concert",
        "venue": {"id": venue.id, "name": venue.name},
    }
