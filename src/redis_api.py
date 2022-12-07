import datetime

import redis
import pytz

from config import params

pool = redis.ConnectionPool(host=f"{params.REDIS_ENDPOINT}", port=6379, db=0)
redis = redis.Redis(connection_pool=pool)


def get_vehicle(vehicle_plate: str) -> datetime.datetime | None:
    """
    Get vehicle expected end time or None if not found
    :param vehicle_plate:
    :return: expected date associated with the vehicle plate
    """
    if redis.exists(vehicle_plate):
        return datetime.datetime.fromtimestamp(
            float(redis.get(vehicle_plate)), tz=pytz.utc
        )
    return None


def set_vehicle(vehicle_plate: str, dt: datetime.datetime) -> None:
    """
    Sets the expected end of charging
    :param vehicle_plate:
    :param dt: expected end of charging
    :return: None
    """
    redis.set(vehicle_plate, dt.timestamp())


def remove_vehicle(vehicle_plate: str) -> None:
    """
    Removes vehicle from redis
    :param vehicle_plate:
    :return: None
    """
    if redis.exists(vehicle_plate):
        redis.delete(vehicle_plate)


def retrieve_all() -> list[tuple[str, datetime.datetime]]:
    """
    :return: all data in redis as a list(plate, endtime)
    """
    vehicles = []
    for key in redis.keys():
        vehicles.append(
            (
                key.decode(),
                datetime.datetime.fromtimestamp(
                    float(redis.get(key.decode())), tz=pytz.utc
                ),
            )
        )
    return vehicles
