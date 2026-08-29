from sqlalchemy.orm import Session
from app.models.academic import Student, SemesterResult, SubjectScore
import logging
from scraper_engine.scraper import scrape_student 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_student_batch(workspace_id: str, records: list[dict], db: Session):
    logger.info(f"Starting background scraping for workspace {workspace_id}")

    for record in records:
        reg_no = record.get("reg_no")
        dob = record.get("dob")
        name = record.get("name", "Unknown")

        if not reg_no or not dob:
            continue

        try:
            # 1. Save Student (Privacy First: No DOB saved!)
            db_student = Student(workspace_id=workspace_id, register_number=str(reg_no), name=str(name))
            db.add(db_student)
            db.commit()
            db.refresh(db_student)

            # 2. Call YOUR Scraper!
            logger.info(f"Scraping results for {reg_no}...")
            
            # Assuming your scraper returns a list of semesters like:
            # [{"semester_number": 1, "sgpa": 8.5, "status": "PASS", "subjects": [...]}]
            scraped_data = scrape_student_results(reg_no, dob) 
            
            if not scraped_data:
                logger.warning(f"No data returned for {reg_no}")
                continue

            # 3. Save to PostgreSQL
            for sem_data in scraped_data:
                db_semester = SemesterResult(
                    student_id=db_student.id,
                    semester_number=sem_data.get('semester_number'),
                    sgpa=sem_data.get('sgpa'),
                    cgpa=sem_data.get('cgpa'),
                    status=sem_data.get('status', 'UNKNOWN')
                )
                db.add(db_semester)
                db.commit()
                db.refresh(db_semester)

                # Save individual subjects
                for sub_data in sem_data.get('subjects', []):
                    db_subject = SubjectScore(
                        semester_id=db_semester.id,
                        subject_code=sub_data.get('subject_code'),
                        subject_name=sub_data.get('subject_name'),
                        internal_marks=sub_data.get('internal_marks'),
                        external_marks=sub_data.get('external_marks'),
                        total_marks=sub_data.get('total_marks'),
                        grade=sub_data.get('grade'),
                        status=sub_data.get('status')
                    )
                    db.add(db_subject)
            
            db.commit()
            logger.info(f"Successfully saved {reg_no} to PostgreSQL!")

        except Exception as e:
            logger.error(f"Failed to process {reg_no}: {str(e)}")
            db.rollback()

    logger.info(f"Finished processing workspace {workspace_id}.")