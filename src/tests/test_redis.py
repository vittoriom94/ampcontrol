import datetime

import pytz

import redis_api
from tests.utils import FakeRedisClient


class TestRedis:
    def test_set_vehicle(self, mocker):
        mocker.patch("redis_api.redis", FakeRedisClient())
        assert not redis_api.redis.exists("XXXXX")
        redis_api.set_vehicle("XXXXX", datetime.datetime.now())
        assert redis_api.redis.exists("XXXXX")

    def test_get_vehicle(self, mocker):
        mocker.patch("redis_api.redis", FakeRedisClient())
        assert redis_api.get_vehicle("XXXXX") is None
        dt = datetime.datetime.now(tz=pytz.utc)
        redis_api.set_vehicle("XXXXX", dt)
        assert redis_api.redis.exists("XXXXX")
        new_dt = redis_api.get_vehicle("XXXXX")
        assert new_dt == dt

    def test_remove_vehicle(self, mocker):
        mocker.patch("redis_api.redis", FakeRedisClient())
        redis_api.set_vehicle("XXXXX", datetime.datetime.now())
        assert redis_api.redis.exists("XXXXX")
        redis_api.remove_vehicle("XXXXX")
        assert not redis_api.redis.exists("XXXXX")
