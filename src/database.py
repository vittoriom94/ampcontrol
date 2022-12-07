from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import params

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{params.DB_USER}:{params.DB_PASSWORD}@{params.DB_ENDPOINT}/{params.DB_NAME}"
)


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()
