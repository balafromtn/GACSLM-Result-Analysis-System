from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    workspace_key = Column(String, unique=True, index=True, nullable=False) # e.g., "2024_BSC_CS_SEM5"
    name = Column(String, nullable=False)  # Display name
    owner_id = Column(String, nullable=False, index=True) # ID of the Tutor/HOD
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    students = relationship("Student", back_populates="workspace", cascade="all, delete-orphan")

class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    register_number = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    community = Column(String, nullable=True)
    dob = Column(String, nullable=True) # Confidential DOB stored per user request
    degree_branch = Column(String, nullable=True)
    
    # Scraping tracking
    scraping_status = Column(String, default="pending") # pending, scraping, completed, failed, retrying
    scraping_error = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="students")
    semesters = relationship("SemesterResult", back_populates="student", cascade="all, delete-orphan")

class SemesterResult(Base):
    __tablename__ = "semester_results"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    semester_number = Column(Integer, nullable=False)
    semester_roman = Column(String, nullable=True)
    exam_month_year = Column(String, nullable=True)
    
    sgpa = Column(Float, nullable=True)
    cgpa = Column(Float, nullable=True)
    total_score = Column(Integer, nullable=True)
    average_score = Column(Float, nullable=True)
    arrear_count = Column(Integer, default=0)
    status = Column(String, nullable=False) # e.g., "PASS", "FAIL"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("Student", back_populates="semesters")
    subjects = relationship("SubjectScore", back_populates="semester", cascade="all, delete-orphan")

class SubjectScore(Base):
    __tablename__ = "subject_scores"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    semester_id = Column(String, ForeignKey("semester_results.id"), nullable=False)
    subject_code = Column(String, nullable=False)
    subject_name = Column(String, nullable=False)
    internal_marks = Column(Integer, nullable=True)
    external_marks = Column(Integer, nullable=True)
    total_marks = Column(Integer, nullable=False)
    grade = Column(String, nullable=True)
    status = Column(String, nullable=False) # e.g., "PASS", "FAIL", "ABSENT"

    # Relationships
    semester = relationship("SemesterResult", back_populates="subjects")