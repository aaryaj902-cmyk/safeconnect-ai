from sqlalchemy import Column, String, Integer

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    industry = Column(String, nullable=True)
    headquarters = Column(String, nullable=True)
    official_domain = Column(String, nullable=True)
    founded_year = Column(Integer, nullable=True)
    trust_status = Column(String, nullable=False, default="unknown")  # verified | flagged | unknown
    trust_score = Column(Integer, nullable=False, default=50)
    employee_count = Column(Integer, nullable=True)
    report_count = Column(Integer, default=0)
    notes = Column(String, nullable=True)
