import re

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from backoffice.application import create_app
from backoffice.models import Admin
from events.models import Event
from tests.factories import VenueFactory


@pytest.fixture
def admin_client(monkeypatch, connection):
    monkeypatch.setenv("ADMIN_SECRET_KEY", "test-admin-session-key")
    monkeypatch.setenv("ADMIN_PASSWORD_SALT", "test-admin-password-salt")
    app = create_app(
        session_factory=sessionmaker(
            bind=connection,
            join_transaction_mode="create_savepoint",
        )
    )
    app.config.update(TESTING=True)
    return app.test_client()


def csrf_token(response):
    return re.search(
        r'name="csrf_token"[^>]*value="([^"]+)"', response.text
    ).group(1)


@pytest.fixture
def admin_account(admin_client):
    result = admin_client.application.test_cli_runner().invoke(
        args=["create-admin", "--email", "organizer@example.com"],
        input="concert-password\nconcert-password\n",
    )
    assert result.exit_code == 0, result.output


@pytest.fixture
def authenticated_admin(admin_client, admin_account):
    login = admin_client.get("/login")
    response = admin_client.post(
        "/login",
        data={
            "email": "organizer@example.com",
            "password": "concert-password",
            "csrf_token": csrf_token(login),
        },
    )
    assert response.status_code == 302
    assert response.location == "/"
    return admin_client


def test_create_admin_rejects_email_with_different_case(
    admin_client, admin_account, session
):
    result = admin_client.application.test_cli_runner().invoke(
        args=["create-admin", "--email", "Organizer@Example.com"],
        input="another-password\nanother-password\n",
    )

    assert result.exit_code == 1
    assert "An admin with this email already exists." in result.output
    assert len(session.scalars(select(Admin)).all()) == 1


def test_backoffice_is_served_by_admin_app_only(client, admin_client):
    assert client.get("/").status_code == 404
    assert client.get("/login").status_code == 404
    assert admin_client.get("/login").status_code == 200


@pytest.mark.parametrize("path", ["/", "/events/", "/events/new/"])
def test_admin_pages_require_login(admin_client, path):
    response = admin_client.get(path)

    assert response.status_code == 302
    assert response.location == "/login"


def test_create_event_at_existing_venue(authenticated_admin, session):
    venue = VenueFactory(name="Main Hall")

    create_page = authenticated_admin.get("/events/new/")
    assert create_page.status_code == 200
    assert "Main Hall" in create_page.text

    response = authenticated_admin.post(
        "/events/new/",
        data={
            "name": "Evening Concert",
            "starts_at": "2027-06-01 19:00:00",
            "venue": str(venue.id),
            "csrf_token": csrf_token(create_page),
        },
    )
    assert response.status_code == 302, response.text

    event = session.scalar(select(Event).where(Event.name == "Evening Concert"))
    assert event.venue_id == venue.id
    assert event.starts_at.isoformat() == "2027-06-01T19:00:00"

    listing = authenticated_admin.get("/events/")
    assert listing.status_code == 200
    assert "Evening Concert" in listing.text
    assert "Main Hall" in listing.text
    assert 'href="/events/new/' in listing.text


def test_event_creation_requires_csrf_token(authenticated_admin, session):
    venue = VenueFactory()

    response = authenticated_admin.post(
        "/events/new/",
        data={
            "name": "Evening Concert",
            "starts_at": "2027-06-01 19:00:00",
            "venue": str(venue.id),
        },
    )

    assert response.status_code == 400
    assert session.scalar(select(Event).where(Event.name == "Evening Concert")) is None


def test_wrong_password_does_not_log_in(admin_client, admin_account):
    login = admin_client.get("/login")
    response = admin_client.post(
        "/login",
        data={
            "email": "organizer@example.com",
            "password": "wrong-password",
            "csrf_token": csrf_token(login),
        },
    )

    assert response.status_code == 200
    assert admin_client.get("/events/").location == "/login"


def test_admin_can_log_out(authenticated_admin):
    home = authenticated_admin.get("/")
    assert "organizer@example.com" in home.text

    response = authenticated_admin.post(
        "/logout", data={"csrf_token": csrf_token(home)}
    )

    assert response.status_code == 302
    assert response.location == "/login"
    assert authenticated_admin.get("/events/").location == "/login"
