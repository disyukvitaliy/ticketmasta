import os

import click
from flask import Flask
from flask_admin import Admin as AdminUI
from flask_security import Security, SQLAlchemySessionUserDatastore, hash_password
from flask_wtf import CSRFProtect
from sqlalchemy.orm import scoped_session

from backoffice.models import Admin, AdminRole
from backoffice.views import BackofficeIndex, EventView
from events.models import Event


def create_app(session_factory):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ["ADMIN_SECRET_KEY"],
        SECURITY_PASSWORD_SALT=os.environ["ADMIN_PASSWORD_SALT"],
        SECURITY_POST_LOGIN_VIEW="/",
        SECURITY_POST_LOGOUT_VIEW="/login",
        SECURITY_LOGOUT_METHODS=["POST"],
        SECURITY_REGISTERABLE=False,
        SESSION_COOKIE_NAME="admin_session",
    )

    session = scoped_session(session_factory)

    @app.teardown_appcontext
    def remove_session(error=None):
        session.remove()

    CSRFProtect(app)
    datastore = SQLAlchemySessionUserDatastore(session, Admin, AdminRole)
    Security(app, datastore)

    admin = AdminUI(
        app,
        name="Ticketmasta",
        url="/",
        index_view=BackofficeIndex(url="/"),
    )
    admin.add_view(
        EventView(Event, session, name="Events", endpoint="events", url="/events")
    )

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_admin(email, password):
        """Create an admin account with access to all events."""
        if datastore.find_user(case_insensitive=True, email=email):
            raise click.ClickException("An admin with this email already exists.")

        datastore.create_user(
            email=email,
            password=hash_password(password),
            active=True,
        )
        datastore.commit()
        click.echo(f"Created admin {email}.")

    return app
