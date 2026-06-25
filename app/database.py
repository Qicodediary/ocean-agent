"""
Database models and connection management
SQLite for simplicity, can be switched to PostgreSQL in production
"""

from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Get relative path from project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_PROJECT_ROOT, "ocean_model.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class JobRecord(Base):
    """Database model for storing job execution records"""
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True, index=True)
    station = Column(String, index=True)
    model = Column(String)
    scenario = Column(String)
    output_type = Column(String)
    start_year = Column(Integer)
    end_year = Column(Integer)
    
    status = Column(String)  # queued, running, finished, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Performance metrics (seconds)
    total_time = Column(Float, nullable=True)
    data_load_time = Column(Float, nullable=True)
    model_run_time = Column(Float, nullable=True)
    plotting_time = Column(Float, nullable=True)
    
    # Results summary
    mean_surface_phytoplankton = Column(Float, nullable=True)
    mean_subsurface_phytoplankton = Column(Float, nullable=True)
    mean_chlorophyll = Column(Float, nullable=True)
    mean_mld = Column(Float, nullable=True)
    
    # Output file paths (relative)
    plot_path = Column(String, nullable=True)
    trend_plot_path = Column(String, nullable=True)
    trend_summary_csv = Column(String, nullable=True)
    data_path = Column(String, nullable=True)
    
    error_message = Column(Text, nullable=True)
    
    # Additional metadata
    metadata_json = Column(JSON, nullable=True)


# Initialize database
def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
