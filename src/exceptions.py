class VehicleDoesNotExistError(Exception):
    def __init__(self, plate):
        super().__init__(f"The vehicle with plate {plate} does not exist.")
