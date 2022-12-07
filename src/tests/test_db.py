import pytest
import sqlalchemy.exc

import models
from tests.utils import db_session


class TestDatabaseVehicleModel:
    def test_no_vehicles_exist(self, db_session):
        assert db_session.query(models.Vehicle).count() == 0

    def test_add_vehicle_correctly(self, db_session):
        assert db_session.query(models.Vehicle).count() == 0
        vehicle = models.Vehicle(
            plate="XXXXX", current_charge=0, total_charge=1000, desired_percentage=50
        )
        db_session.add(vehicle)
        db_session.commit()
        assert db_session.query(models.Vehicle).first() == vehicle

    def test_add_multiple_vehicles(self, db_session):
        assert db_session.query(models.Vehicle).count() == 0
        first = models.Vehicle(
            plate="XXXXX1", current_charge=0, total_charge=1000, desired_percentage=50
        )

        second = models.Vehicle(
            plate="XXXXX2", current_charge=0, total_charge=1000, desired_percentage=50
        )
        db_session.bulk_save_objects([first, second])
        db_session.commit()
        assert (
            db_session.query(models.Vehicle)
            .filter(models.Vehicle.plate == first.plate)
            .first()
            is not None
        )
        assert (
            db_session.query(models.Vehicle)
            .filter(models.Vehicle.plate == second.plate)
            .first()
            is not None
        )

    def test_add_same_plate_raises_error(self, db_session):
        assert db_session.query(models.Vehicle).count() == 0
        first = models.Vehicle(
            plate="XXXXX", current_charge=0, total_charge=1000, desired_percentage=50
        )

        second = models.Vehicle(
            plate="XXXXX", current_charge=0, total_charge=1000, desired_percentage=50
        )
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.bulk_save_objects([first, second])

    def test_negative_desired_charge(self, db_session):
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.add(
                models.Vehicle(
                    plate="XXXXX",
                    current_charge=-1,
                    total_charge=100,
                    desired_percentage=50,
                )
            )
            db_session.commit()

    def test_negative_total_charge(self, db_session):
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.add(
                models.Vehicle(
                    plate="XXXXX",
                    current_charge=100,
                    total_charge=-1,
                    desired_percentage=50,
                )
            )
            db_session.commit()

    def test_desired_higher_than_total_charge(self, db_session):
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.add(
                models.Vehicle(
                    plate="XXXXX",
                    current_charge=100,
                    total_charge=10,
                    desired_percentage=50,
                )
            )
            db_session.commit()

    def test_percentage_out_of_bounds(self, db_session):
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.add(
                models.Vehicle(
                    plate="XXXXX",
                    current_charge=50,
                    total_charge=100,
                    desired_percentage=-1,
                )
            )
            db_session.commit()
        db_session.rollback()
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.add(
                models.Vehicle(
                    plate="XXXXX",
                    current_charge=50,
                    total_charge=100,
                    desired_percentage=105,
                )
            )
            db_session.commit()
