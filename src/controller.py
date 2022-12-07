import datetime
import logging
import typing

import httpx
import pytz
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
import redis_api
from exceptions import VehicleDoesNotExistError


async def import_data(url: str, session: Session) -> int:
    """
    Import data from a URL
    :param url: direct link to a CSV file without header
    :param session: db session
    :return: imported vehicles
    """
    count = 0

    def create_vehicle_callable(line: str) -> None:
        """
        closure that updates count variable
        """
        try:
            vehicle = _parse_line(line)
            existing_vehicle = (
                session.query(models.Vehicle).filter_by(plate=vehicle.plate).first()
            )
            if not existing_vehicle:
                session.add(vehicle)
            else:
                vehicle.id = existing_vehicle.id
                session.merge(vehicle)
            session.commit()
            redis_api.set_vehicle(
                vehicle.plate,
                datetime.datetime.fromtimestamp(
                    vehicle.start_time.timestamp()
                    + _calculate_end_time(
                        vehicle.current_charge,
                        vehicle.total_charge,
                        vehicle.desired_percentage,
                    )
                ),
            )
            nonlocal count
            count += 1
        except Exception as ex:
            session.rollback()
            logging.error(f"Could not import vehicle: {line} due to: {ex}")

    await _stream_data(url, create_vehicle_callable)
    return count


def update_and_retrieve_ready(session: Session) -> list[models.Vehicle]:
    """
    Retrieve a list of vehicles ready for pickup and update DB with current charge of all vehicles
    :param session: db session
    :return: list of vehicles ready for pickup
    """
    vehicles = redis_api.retrieve_all()
    current_time = datetime.datetime.now(tz=pytz.utc)

    ready_vehicles = []
    for plate, end_time in vehicles:
        vehicle = session.execute(
            select(models.Vehicle).filter_by(plate=plate)
        ).scalar_one()
        vehicle.current_charge = _calculate_current_charge(
            vehicle.current_charge,
            vehicle.total_charge,
            vehicle.start_time,
            current_time,
        )
        vehicle.start_time = current_time
        if end_time <= current_time:
            ready_vehicles.append(vehicle)
    session.commit()
    return ready_vehicles


def remove_vehicle(plate: str, session: Session) -> int:
    """
    Remove a vehicle from the system.
    This means that the vehicle is removed from the db and is set as not parked in the DB
    :param plate: vehicle plate
    :param session: db session
    :return: current charge of the vehicle
    """
    if not redis_api.get_vehicle(plate):
        raise VehicleDoesNotExistError(plate)
    redis_api.remove_vehicle(plate)
    vehicle = session.execute(
        select(models.Vehicle).filter_by(plate=plate)
    ).scalar_one()
    vehicle.parked = False
    current_charge = _calculate_current_charge(
        vehicle.current_charge,
        vehicle.total_charge,
        vehicle.start_time,
        datetime.datetime.now(tz=pytz.utc),
    )
    vehicle.current_charge = current_charge
    session.commit()
    return current_charge


def get_vehicle(plate: str) -> [datetime.datetime, bool]:
    """
    Retrieve the expected datetime of completed charge and if the charge is completed.
    Raises VehicleDoesNotExistError if vehicle plate is not found in redis

    :param plate: vehicle plate
    :return: expected date, completed
    """
    expected_end_of_charge = redis_api.get_vehicle(plate)
    if not expected_end_of_charge:
        raise VehicleDoesNotExistError(plate)
    return expected_end_of_charge, expected_end_of_charge <= datetime.datetime.now(
        tz=pytz.utc
    )


def _calculate_end_time(current_charge: int, total_charge: int, desired: int) -> int:
    current_percentage = current_charge * 100 / total_charge
    return max(0, int(desired - current_percentage))


def _parse_line(line: str) -> models.Vehicle:
    plate, current_charge, total_charge, desired_percentage = line.split(",")
    return models.Vehicle(
        plate=plate,
        current_charge=int(current_charge),
        total_charge=int(total_charge),
        desired_percentage=int(desired_percentage),
        start_time=datetime.datetime.now(tz=pytz.utc),
        parked=True,
    )


async def _stream_data(url: str, add_vehicle_callable: typing.Callable) -> None:
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            async for line in response.aiter_lines():
                add_vehicle_callable(line)


def _calculate_current_charge(
    current_charge: int,
    total_charge: int,
    start_time: datetime.datetime,
    current_time: datetime.datetime,
) -> int:
    elapsed_time = (current_time - start_time).seconds

    charged = elapsed_time

    return min(total_charge, int(current_charge + (total_charge * charged / 100)))
