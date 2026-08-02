from app.extensions import engine
from app.models import Base


def create_database():

    Base.metadata.create_all(
        bind=engine
    )
