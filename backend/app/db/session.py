from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

import numpy as np
from psycopg2.extensions import register_adapter, AsIs

# Fix numpy types for psycopg2
register_adapter(np.int64, lambda val: AsIs(int(val)))
register_adapter(np.int32, lambda val: AsIs(int(val)))
register_adapter(np.float64, lambda val: AsIs(float(val)))
register_adapter(np.float32, lambda val: AsIs(float(val)))

# Connection to the database
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for all our models to inherit from
Base = declarative_base()


def get_db():
    """
    FastAPI Dependency 
    Provides a database session and closes it after the request is done.
    Use in endpoints: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()