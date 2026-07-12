import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default URL inside docker network
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://wildcard:wildcardpassword@db:5432/wildcard_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
