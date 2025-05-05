import os

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    message_ts = Column(String, nullable=False)
    text = Column(String, nullable=False)

class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(Integer, ForeignKey("announcements.id"), nullable=False)
    user_id = Column(String, nullable=False)

class ReadReceipt(Base):
    __tablename__ = "read_receipts"
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)