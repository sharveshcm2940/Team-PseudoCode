import os
os.environ["DATABASE_URL"] = "sqlite://"
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.seed import seed

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
@pytest.fixture()
def db():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    with TestingSession() as session:
        seed(session); yield session
