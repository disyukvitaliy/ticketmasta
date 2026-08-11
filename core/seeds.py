import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["CORE_DB_DSN"])

with engine.begin() as connection:
    connection.execute(
        text(
            "TRUNCATE ticket_holds, ticket_types, events, venues "
            "RESTART IDENTITY CASCADE"
        )
    )

    venues = [
        ("Riverside Zoo", "zoo"),
        ("Meadowlark Park", "park"),
        ("Willow Creek Gardens", "garden"),
        ("North Star Science Centre", "science_centre"),
        ("Cedar Park", "park"),
        ("Maplewood Zoo", "zoo"),
        ("The Glasshouse", "gallery"),
        ("Sunset Field", "park"),
        ("Rosewood Botanical Garden", "garden"),
        ("Seabird Aquarium", "aquarium"),
        ("Oak & Ivy Gardens", "garden"),
        ("The Foundry", "gallery"),
        ("The Orangery", "garden"),
        ("Foxglove Farm", "farm"),
        ("Moonrise Park", "park"),
        ("Fernbank Nature Reserve", "nature_reserve"),
        ("The Atrium", "gallery"),
        ("Pine Ridge Park", "park"),
        ("City Museum of Art", "museum"),
        ("Juniper Fields", "park"),
        ("Wildwood Safari Park", "zoo"),
        ("The Conservatory", "gallery"),
        ("Birchwood Park", "park"),
        ("Redwood Wildlife Park", "zoo"),
        ("Market Square", "market"),
        ("The Riverside Gallery", "gallery"),
        ("Hilltop Gardens", "garden"),
        ("Brookside Zoo", "zoo"),
        ("The Old Library", "museum"),
        ("Summit Nature Park", "nature_reserve"),
        ("Harbour Discovery Museum", "museum"),
        ("Lakeside Wildlife Reserve", "nature_reserve"),
        ("Greenmarket Square", "market"),
        ("Museum of Natural History", "museum"),
        ("Bluebell Farm", "farm"),
        ("Riverside Promenade", "park"),
        ("Maritime Museum", "museum"),
        ("Woodland Adventure Park", "zoo"),
        ("Golden Meadow", "garden"),
        ("Children's Discovery Museum", "science_centre"),
        ("Riverbend Botanic Garden", "garden"),
        ("Coastal Aquarium", "aquarium"),
        ("Museum of Science", "science_centre"),
        ("Applewood Orchard", "farm"),
        ("Elmwood Common", "park"),
        ("Contemporary Art Gallery", "gallery"),
        ("Hawthorn Wildlife Sanctuary", "nature_reserve"),
        ("Canal Side Park", "park"),
        ("Railway Heritage Museum", "historic_site"),
        ("Meadowbrook Farm", "farm"),
    ]

    venue_ids = []
    ticket_groups = {
        "aquarium": "wildlife",
        "farm": "wildlife",
        "garden": "outdoor",
        "gallery": "culture",
        "historic_site": "culture",
        "market": "market",
        "museum": "culture",
        "nature_reserve": "wildlife",
        "park": "outdoor",
        "science_centre": "culture",
        "zoo": "wildlife",
    }

    for name, venue_type in venues:
        venue_id = connection.execute(
            text("INSERT INTO venues (name) VALUES (:name) RETURNING id"),
            {"name": name},
        ).scalar_one()
        venue_ids.append((venue_id, name, venue_type, ticket_groups[venue_type]))

    ticket_types = {
        "wildlife": [
            ("Adult", 2400, 120),
            ("Child", 1400, 80),
            ("Family ticket", 6500, 30),
        ],
        "outdoor": [
            ("General admission", 3000, 200),
            ("Day pass", 5500, 50),
            ("Premium access", 8500, 20),
        ],
        "culture": [
            ("Entry", 1800, 100),
            ("Guided tour", 3200, 40),
            ("Evening access", 6000, 15),
        ],
        "market": [
            ("Entry", 1200, 200),
            ("Tasting pass", 3000, 80),
            ("All-day pass", 5000, 30),
        ],
    }

    event_names = {
        "zoo": [
            "Wildlife Encounters",
            "After-Dark Safari",
            "Conservation Weekend",
        ],
        "park": [
            "Summer Food Festival",
            "Outdoor Cinema",
            "Weekend Makers Market",
        ],
        "garden": [
            "Spring Flower Festival",
            "Garden After Hours",
            "Botanical Workshop",
        ],
        "science_centre": [
            "Space Discovery Weekend",
            "Future Makers Fair",
            "Family Experiment Day",
        ],
        "gallery": [
            "Artist Talk and Tour",
            "New Collection Opening",
            "Late Night Gallery",
        ],
        "aquarium": [
            "Ocean After Dark",
            "Marine Life Discovery Day",
            "Coral Conservation Weekend",
        ],
        "farm": [
            "Harvest Festival",
            "Farm Animals Weekend",
            "Orchard Picnic Day",
        ],
        "nature_reserve": [
            "Dawn Wildlife Walk",
            "Nature Photography Day",
            "Conservation Volunteers Day",
        ],
        "market": [
            "Street Food Festival",
            "Craft Market Weekend",
            "Local Producers Fair",
        ],
        "museum": [
            "After Hours at the Museum",
            "New Exhibition Opening",
            "Family Discovery Day",
        ],
        "historic_site": [
            "Railway Heritage Weekend",
            "History Walk and Tour",
            "Restoration Open Day",
        ],
    }

    for number in range(1, 501):
        starts_at = datetime(2026, 4, 1, tzinfo=UTC) + timedelta(days=number - 1)
        venue_id, venue_name, venue_type, ticket_group = venue_ids[
            (number - 1) % len(venue_ids)
        ]
        event_name = event_names[venue_type][(number - 1) % 3]
        event_id = connection.execute(
            text(
                "INSERT INTO events (name, venue_id, starts_at) "
                "VALUES (:name, :venue_id, :starts_at) RETURNING id"
            ),
            {
                "name": f"{event_name} at {venue_name}",
                "venue_id": venue_id,
                "starts_at": starts_at,
            },
        ).scalar_one()
        connection.execute(
            text(
                "INSERT INTO ticket_types (event_id, name, price_cents, quantity) "
                "VALUES (:event_id, :name, :price_cents, :quantity)"
            ),
            [
                {
                    "event_id": event_id,
                    "name": name,
                    "price_cents": price_cents,
                    "quantity": quantity,
                }
                for name, price_cents, quantity in ticket_types[ticket_group]
            ],
        )

print("Created 50 venues, 500 events, and 1,500 ticket types.")
