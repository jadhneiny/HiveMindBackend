from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://neondb_owner:s7pfrUzokYw0@ep-patient-tree-a2ipxqne.eu-central-1.aws.neon.tech/neondb?sslmode=require"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

# Create a SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()
