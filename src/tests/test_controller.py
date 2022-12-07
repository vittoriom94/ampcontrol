import datetime

import pytest

import controller
import models
import redis_api
from tests.utils import FakeRedisClient
from exceptions import VehicleDoesNotExistError
from tests.utils import db_session


def add_vehicle(
    session,
    redis_client,
    plate="ABCDE",
    current_charge=0,
    total_charge=1000,
    desired=50,
):
    vehicle = models.Vehicle(
        plate=plate,
        current_charge=current_charge,
        desired_percentage=desired,
        total_charge=total_charge,
    )

    time_in_seconds = controller._calculate_end_time(
        current_charge, total_charge, desired
    )

    session.add(vehicle)
    session.commit()
    redis_client.set(vehicle.plate, vehicle.start_time.timestamp() + time_in_seconds)
    return vehicle


async def stream_data(url, callback, data):
    for line in data.splitlines():
        callback(line)


class TestVehicle:
    def test_get_vehicle_exists(self, mocker):
        mocker.patch("redis_api.redis", FakeRedisClient())
        redis_api.redis.set("ABCDE", datetime.datetime.now().timestamp())
        date, ready = controller.get_vehicle("ABCDE")
        assert ready

        redis_api.redis.set("ABCDE", datetime.datetime.now().timestamp() + 10000)
        date, ready = controller.get_vehicle("ABCDE")
        assert not ready

    def test_get_vehicle_not_exists(self, mocker):
        mocker.patch("redis_api.redis", FakeRedisClient())
        with pytest.raises(VehicleDoesNotExistError):
            controller.get_vehicle("ABCDE")

    def test_remove_vehicle_exists(self, mocker, db_session):
        mocker.patch("redis_api.redis", FakeRedisClient())
        v = add_vehicle(db_session, redis_api.redis)
        charge = controller.remove_vehicle(v.plate, db_session)
        assert charge is not None

    def test_remove_vehicle_not_exists(self, mocker):
        mocker.patch("redis_api.redis", FakeRedisClient())
        with pytest.raises(VehicleDoesNotExistError):
            controller.remove_vehicle("ABCDE", None)


class TestRetrieve:
    def test_update_and_retrieve_ready(self, mocker, db_session):
        mocker.patch("redis_api.redis", FakeRedisClient())
        add_vehicle(
            db_session,
            redis_api.redis,
            "A",
            current_charge=50,
            total_charge=100,
            desired=20,
        )
        add_vehicle(
            db_session,
            redis_api.redis,
            "B",
            current_charge=50,
            total_charge=100,
            desired=90,
        )
        add_vehicle(
            db_session,
            redis_api.redis,
            "C",
            current_charge=50,
            total_charge=100,
            desired=10,
        )
        add_vehicle(
            db_session,
            redis_api.redis,
            "D",
            current_charge=50,
            total_charge=100,
            desired=80,
        )

        ready = controller.update_and_retrieve_ready(db_session)
        assert len(ready) == 2


class TestImport:
    data = """A0001,50,100,20
A0002,50,100,90
A0003,50,100,10
A0004,50,100,80"""

    @pytest.mark.anyio
    async def test_import_data(self, mocker, db_session):
        mocker.patch("redis_api.redis", FakeRedisClient())
        mocker.patch(
            "controller._stream_data",
            lambda *args, **kwargs: stream_data(data=self.data, *args, **kwargs),
        )
        await controller.import_data("", db_session)
        assert db_session.query(models.Vehicle).count() == 4
