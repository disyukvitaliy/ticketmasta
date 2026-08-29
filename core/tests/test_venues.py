def test_list_venues_returns_venues_ordered_by_name(client, factory):
    zebra_hall = factory.create_venue(name="Zebra Hall")
    alpha_arena = factory.create_venue(name="Alpha Arena")

    response = client.get("/venues")

    assert response.status_code == 200
    assert response.json == [
        {"id": alpha_arena.id, "name": "Alpha Arena"},
        {"id": zebra_hall.id, "name": "Zebra Hall"},
    ]
