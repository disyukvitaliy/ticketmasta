from models import Venue


class Factory:
    def __init__(self, session):
        self.session = session

    def create_venue(self, **attrs):
        venue = Venue(**attrs)
        self.session.add(venue)
        self.session.flush()
        return venue
