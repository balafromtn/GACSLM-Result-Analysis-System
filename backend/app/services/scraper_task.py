from sqlalchemy.orm import Session
from app.models.academic import Student, SemesterResult, SubjectScore
from app.core.database import SessionLocal
import logging
from scraper_engine.scraper import scrape_student, create_driver
from scraper_engine.parser import parse_html_table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_student_batch(workspace_id: str, records: list[dict]):
    logger.info(f"Starting background scraping for workspace {workspace_id}")

    # 1. Initialize the Selenium WebDriver ONCE for the whole batch
    driver = create_driver(headless=True)
    db = SessionLocal()

    try:
        for record in records:
            reg_no = record.get("reg_no")
            dob = record.get("dob")
            name = record.get("name", "Unknown")
            gender = record.get("gender", "Unknown")

            if not reg_no or not dob:
                continue

            try:
                # Save Student (Privacy First: No DOB saved!)
                db_student = Student(
                    workspace_id=workspace_id, 
                    register_number=str(reg_no), 
                    name=str(name),
                    gender=str(gender)
                )
                db.add(db_student)
                db.commit()
                db.refresh(db_student)

                # 2. Call the Scraper WITH the driver!
                logger.info(f"Scraping results for {reg_no}...")
                table_html = scrape_student(driver, reg_no, dob) 
                
                if not table_html:
                    logger.warning(f"No data returned for {reg_no}")
                    continue

                # 3. Parse the raw HTML into the dictionary structure
                scraped_data = parse_html_table(table_html) 

                # 4. Save to PostgreSQL
                for sem_data in scraped_data:
                    # Update student with newly parsed details if available
                    if sem_data.get('dob') and sem_data.get('dob') != 'UNKNOWN':
                        db_student.dob = sem_data.get('dob')
                    else:
                        db_student.dob = dob # Fallback to CSV dob
                        
                    if sem_data.get('degree_branch') and sem_data.get('degree_branch') != 'UNKNOWN':
                        db_student.degree_branch = sem_data.get('degree_branch')
                        
                    db.commit()

                    db_semester = SemesterResult(
                        student_id=db_student.id,
                        semester_number=sem_data.get('semester_number', 1),
                        semester_roman=sem_data.get('semester_roman'),
                        exam_month_year=sem_data.get('exam_month_year'),
                        sgpa=sem_data.get('sgpa'),
                        cgpa=sem_data.get('cgpa'),
                        total_score=sem_data.get('total_score'),
                        average_score=sem_data.get('average_score'),
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
    
    finally:
        # ALWAYS quit the driver when the batch is done to prevent memory leaks!
        driver.quit()
        db.close()
        logger.info(f"Finished processing workspace {workspace_id}. Browser and DB session closed.")