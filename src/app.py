import logging

import uvicorn as uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

import controller
import exceptions
import models
from database import engine, get_db

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/data", response_model=models.GetDataResponse)
async def get_data(*, session: Session = Depends(get_db)):
    """
    Retrieve all plates that have reached the desired charge.
    """
    vehicles_ready = controller.update_and_retrieve_ready(session)
    return models.GetDataResponse(ready=[vehicle.plate for vehicle in vehicles_ready])


@app.post(
    "/data", status_code=status.HTTP_201_CREATED, response_model=models.PostDataResponse
)
async def post_data(data: models.PostDataBody, session: Session = Depends(get_db)):
    """
    Import data from a CSV or TXT direct url.
    The file should be in the following format (no header):
    plate (str),current_charge (int: Ah,total_charge (int: Ah),desired_charge (int: %),
    """
    imported = await controller.import_data(data.url, session)
    if not imported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not import articles"
        )
    return models.PostDataResponse(imported=imported)


@app.get("/vehicle/{plate}", response_model=models.GetVehicleResponse)
def get_vehicle(plate: str):
    """
    Retrieve the status of a vehicle
    """
    try:
        end_date, done = controller.get_vehicle(plate)
    except exceptions.VehicleDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{plate} not found"
        )
    return models.GetVehicleResponse(estimated=end_date, completed=done)


@app.delete("/vehicle/{plate}", response_model=models.DeleteVehicleResponse)
def delete_vehicle(plate: str, session: Session = Depends(get_db)):
    """
    Remove a vehicle from the system
    """
    try:
        current_charge = controller.remove_vehicle(plate, session)
    except exceptions.VehicleDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{plate} not found"
        )
    return models.DeleteVehicleResponse(current_charge=current_charge)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
