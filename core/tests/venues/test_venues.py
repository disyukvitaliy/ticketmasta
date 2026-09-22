from tests.factories import VenueFactory


def test_list_venues_returns_venues_ordered_by_name(client):
    zebra_hall = VenueFactory(name="Zebra Hall")
    alpha_arena = VenueFactory(name="Alpha Arena")

    response = client.get("/venues")

    assert response.status_code == 200
    assert response.json == [
        {"id": alpha_arena.id, "name": "Alpha Arena"},
        {"id": zebra_hall.id, "name": "Zebra Hall"},
    ]


def test_get_venue_returns_venue(client):
    venue = VenueFactory(name="Alpha Arena")

    response = client.get(f"/venues/{venue.id}")

    assert response.status_code == 200
    assert response.json == {"id": venue.id, "name": "Alpha Arena"}
