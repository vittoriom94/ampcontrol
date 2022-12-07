# AmpControl
## Instructions
run `docker-compose up` and go to `localhost:5000/docs` to read the documentation

## Goal of the project
The goal of the project is to develop an application that can be used to track electric vehicles inside a parking lot and
check their battery charge levels.

The application serves four main features:
- Import vehicles from a csv file 
  - The CSV is expected through a direct url.
  - The format of the file is vehicle,current_charge,total_charge,desired_percentage
- Retrieve vehicles that have reached the desired charge and update the current charge
- Check if a vehicle is ready and when it will be ready
- Remove vehicle from the system

## Design
THe following components have been chosen for the application
- Server: FastAPI
  - As a modern python web framework, FastAPI allows the application to easily scale and be ready to support big import files or multiple concurrent requests that request the vehicle status.
  - Uvicorn has been chosen as ASGI server, as it is the standard for this type of application
- Database: PostgreSQL
  - the RDBMS is used so that data on vehicles can be stored and used for statistics or ML purposes
  - A possible use would be to analyze what's the average charge time of vehicles in the parking lot and understand if the available capacity of it is enough or too much.
  - SQLAlchemy ORM is used for the communication between the application and the db.
    - This helps keeping the code in a "pythonic" way, avoid SQL attacks and be mostly independent of the RDBMS implementation, instead of manually writing queries.
- Database: Redis
  - A Key-Value DB is used so that it is faster to retrieve information on the vehicle
    - Example: if vehicle owners have an app the pokes the info endpoint ("/vehicle/{plate}") by short polling, the requests might overload an RDBMS
  - The database stores the association vehicle_plate -> estimated_date_for_desired_charge
- Testing: PyTest
  - Tests are executed and written using PyTest, this choice was influenced by the availability of a test client in FastAPI that requires PyTest
  - Tests cover all endpoints and main functions used by the application
  - A test coverage has been done, with a 97% code coverage.
- Documentation
  - Endpoints are documented through OpenAPI. PyDantic models are used so that FastAPI is able to automatically generate the documentation
  - OpenAPI documentation is available at "host:port/docs"
- Deployment
  - The application can be deployed through docker-compose with `docker-compose up`.
  - As the application is Dockerized, it can be easily ported to other deployment methods like kubernetes, ECS or external platforms.
  - Required constants can be checked in `config.py`, with additional support for different configuartion extraction methods.

## Endpoints
`POST /data` - Body: `{"url": url}`: Import data from CSV
- Data is extracted from URL source
- For each line, a vehicle is created in the DB and added to Redis with the estimated end of charge date.

`GET /data`: Retrieve vehicles ready, update DB with current times
- Vehicles are extracted from Redis
- Vehicle on DB is updated with current charge
- If vehicle has reached desired charge, it is added to the return list

`GET /vehicle/{plate}`: Retrieve vehicle status
- Vehicle is retrieved from Redis
- current date is compared with end date on redis to check if it is completed

`DELETE /vehicle/{plate}`: Remove vehicle from system
- Vehicle is retrieved and removed from Redis
- Vehicle DB is updated with current charge and parked=False for future uses
- Returns the current charge of the vehicle

## Improvements
- There is currently no deploy pipeline or commmit-hooks. These could be a first addition in order to ensure code quality and consistency.
- End-to-end tests might be added through an application like Postman, the current tests will mock some dependencies, so there might be inconsistencies.
- Most of the code can be ported to async by using aioredis and sqlalchemy[asyncio].
  - An idea could be to read multiple files concurrently and asynchronize the step extract line -> save to db.
- Libraries like Prometheus, OpenTelemetry with Jaeger and Locust could be used for analyzing performances.
- Deployment could be done through terraform


## Personal considerations and roadblocks
- Some technical choice could be simplified, but I tried to keep them for showcasing reasons.
- As my work stack is different from the one used in this project, I faced technical challenges that involve working with new libraries and framework.
  - My usual stack is Django (for DB interaction), Flask, unittest, AWS services
- Most of the time was spent understanding the documentation and solving issues between async and PyTest, sqlalchemy, FastAPI best practices.
  - This also probably led me to writing code that is more similar to those other libraries than the used ones.
    - Example: I haven't used all the features of PyTest and I often tried to write tests like Django and unittest, where fixtures refer to initial data loaded in the DB and mock objects can be defined for all methods in class with a decorator.
