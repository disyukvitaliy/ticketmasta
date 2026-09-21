from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
