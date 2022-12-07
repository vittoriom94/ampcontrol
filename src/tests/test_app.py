import datetime

import pytz
from fastapi import FastAPI
from fastapi.testclient import TestClient

import models
from app import app

from tests.utils import db_session, FakeRedisClient

client = TestClient(app)


def fake_datetime_now(*args, **kwargs):
    return datetime.datetime(year=3000, month=1, day=1, tzinfo=pytz.utc)


class TestApp:

    data_url = "https://pastebin.com/raw/57D2pTWe"  # 17 items, 5 already completed

    def test_app_exists(self):
        assert isinstance(app, FastAPI)

    def test_import_data(self, mocker, db_session):
        mocker.patch("redis_api.redis", FakeRedisClient())
        response = client.post("/data", json={"url": self.data_url})
        assert response.status_code == 201
        assert response.json()["imported"] == db_session.query(models.Vehicle).count()

    def test_read_data(self, mocker, db_session):
        mocker.patch("redis_api.redis", FakeRedisClient())
        response = client.post("/data", json={"url": self.data_url})
        assert response.status_code == 201
        response = client.get("/data")
        assert response.status_code == 200
        assert len(response.json()["ready"]) == 5

    def test_remove_vehicle(self, mocker, db_session):
        mocker.patch("redis_api.redis", FakeRedisClient())
        client.post("/data", json={"url": self.data_url})
        response = client.get("/data")
        plate = response.json()["ready"][0]
        response = client.get(f"/vehicle/{plate}")
        assert response.status_code == 200
        assert response.json()["completed"]
        response = client.delete(f"/vehicle/{plate}")
        assert response.status_code == 200
        assert db_session.query(models.Vehicle).filter_by(parked=False).count() == 1
        assert (
            db_session.query(models.Vehicle).filter_by(parked=False).scalar().plate
            == plate
        )

    def test_reinsert_vehicle(self, mocker, db_session):
        mocker.patch("redis_api.redis", FakeRedisClient())
        client.post("/data", json={"url": self.data_url})
        response = client.get("/data")
        plate = response.json()["ready"][0]
        client.delete(f"/vehicle/{plate}")
        assert (
            db_session.query(models.Vehicle).filter_by(parked=False).scalar().plate
            == plate
        )
        client.post("/data", json={"url": self.data_url})
        assert db_session.query(models.Vehicle).filter_by(parked=False).count() == 0
