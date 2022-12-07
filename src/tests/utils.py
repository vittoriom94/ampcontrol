import pytest

import models
from database import engine, SessionLocal


class FakeRedisClient:
    def __init__(self):
        self.d = {}

    def get(self, key):
        if key in self.d:
            return self.d[key]
        raise KeyError()

    def set(self, key, value):
        self.d[key] = str(value).encode()

    def delete(self, key):
        del self.d[key]

    def exists(self, key):
        return key in self.d

    def keys(self):
        return list(key.encode() for key in self.d.keys())


@pytest.fixture()
def db_session():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(engine)
    session = SessionLocal()
    yield session
    session.close()
    models.Base.metadata.drop_all(bind=engine)
