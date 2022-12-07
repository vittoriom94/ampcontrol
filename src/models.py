import datetime

from pydantic import BaseModel
from sqlalchemy import (
    Integer,
    Column,
    String,
    CheckConstraint,
    DateTime,
    func,
    Boolean,
)
from database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(20), unique=True, index=True)
    current_charge = Column(Integer)
    total_charge = Column(Integer)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    desired_percentage = Column(Integer)
    parked = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(current_charge >= 0, name="check_current_charge_non_negative"),
        CheckConstraint(total_charge >= 0, name="check_total_charge_non_negative"),
        CheckConstraint(
            desired_percentage <= 100,
            name="check_desired_percentage_less_or_equal_than_hundred",
        ),
        CheckConstraint(
            desired_percentage >= 0,
            name="check_desired_percentage_above_or_equal_than_zero",
        ),
        CheckConstraint(
            current_charge <= total_charge,
            name="check_current_charge_not_higher_than_total_charge",
        ),
    )


class PostDataBody(BaseModel):
    url: str


class GetDataResponse(BaseModel):
    ready: list[str]


class PostDataResponse(BaseModel):
    imported: int


class GetVehicleResponse(BaseModel):
    estimated: datetime.datetime
    completed: bool


class DeleteVehicleResponse(BaseModel):
    current_charge: int
