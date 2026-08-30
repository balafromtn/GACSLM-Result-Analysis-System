from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.academic import Student, SemesterResult, SubjectScore
from app.core.config import settings
from groq import Groq

router = APIRouter()

GROQ_API_KEY = settings.GROQ_API_KEY
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@router.get("/analytics/{workspace_id}/summary")
def get_workspace_summary(workspace_id: str, db: Session = Depends(get_db)):
    total_students = db.query(Student).filter(Student.workspace_id == workspace_id).count()
    if total_students == 0:
        raise HTTPException(status_code=404, detail="No students found in this workspace.")

    results = db.query(SemesterResult).join(Student).filter(Student.workspace_id == workspace_id).all()
    
    if not results:
        return {
            "total_students": total_students,
            "status": "Awaiting scraper completion..."
        }

    total_passed = sum(1 for r in results if r.status.upper() == "PASS")
    total_failed = sum(1 for r in results if r.status.upper() != "PASS")
    total_completed = len(results)
    
    valid_sgpas = [r.sgpa for r in results if r.sgpa is not None and r.sgpa > 0]
    avg_sgpa = round(sum(valid_sgpas) / len(valid_sgpas), 2) if valid_sgpas else 0.0

    valid_totals = [r.total_score for r in results if r.total_score is not None and r.total_score > 0]
    highest_mark = max(valid_totals) if valid_totals else 0
    lowest_mark = min(valid_totals) if valid_totals else 0

    return {
        "workspace_id": workspace_id,
        "total_students": total_students,
        "metrics": {
            "passed": total_passed,
            "failed": total_failed,
            "pass_percentage": round((total_passed / total_completed) * 100, 1) if total_completed > 0 else 0,
            "average_sgpa": avg_sgpa,
            "highest_mark": highest_mark,
            "lowest_mark": lowest_mark,
            "total_completed": total_completed
        }
    }

@router.get("/analytics/{workspace_id}/students")
def get_workspace_students(workspace_id: str, db: Session = Depends(get_db)):
    results = db.query(SemesterResult, Student).join(Student).filter(Student.workspace_id == workspace_id).all()
    
    students_data = []
    for sem_res, student in results:
        subjects = db.query(SubjectScore).filter(SubjectScore.semester_id == sem_res.id).all()
        
        failed_subjects = [s.subject_name for s in subjects if s.status.upper() == "FAIL"]
        
        students_data.append({
            "id": student.id,
            "register_number": student.register_number,
            "name": student.name,
            "gender": student.gender,
            "total": sem_res.total_score,
            "average": sem_res.average_score,
            "gpa": sem_res.sgpa,
            "status": sem_res.status,
            "failed_subjects": failed_subjects,
            "trend": "→", # Placeholder for single semester
            "subjects": [{"code": s.subject_code, "name": s.subject_name, "marks": s.total_marks, "grade": s.grade, "status": s.status} for s in subjects]
        })
        
    # Sort by total score descending to assign ranks
    students_data.sort(key=lambda x: x.get("total") or 0, reverse=True)
    
    for i, s in enumerate(students_data):
        s["rank"] = i + 1

    return {"students": students_data}

@router.get("/analytics/{workspace_id}/subjects")
def get_workspace_subjects(workspace_id: str, db: Session = Depends(get_db)):
    results = db.query(SemesterResult).join(Student).filter(Student.workspace_id == workspace_id).all()
    sem_ids = [r.id for r in results]
    
    if not sem_ids:
        return {"subjects": []}
        
    subjects = db.query(SubjectScore).filter(SubjectScore.semester_id.in_(sem_ids)).all()
    
    subject_stats = {}
    for s in subjects:
        if s.subject_code not in subject_stats:
            subject_stats[s.subject_code] = {"name": s.subject_name, "total_marks": 0, "count": 0, "passed": 0}
            
        subject_stats[s.subject_code]["total_marks"] += s.total_marks
        subject_stats[s.subject_code]["count"] += 1
        if s.status.upper() == "PASS":
            subject_stats[s.subject_code]["passed"] += 1
            
    final_stats = []
    for code, stats in subject_stats.items():
        avg = round(stats["total_marks"] / stats["count"], 1) if stats["count"] > 0 else 0
        pass_rate = round((stats["passed"] / stats["count"]) * 100, 1) if stats["count"] > 0 else 0
        final_stats.append({
            "code": code,
            "name": stats["name"],
            "average": avg,
            "pass_rate": pass_rate
        })
        
    return {"subjects": final_stats}

@router.get("/analytics/{workspace_id}/distribution")
def get_workspace_distribution(workspace_id: str, db: Session = Depends(get_db)):
    results = db.query(SemesterResult).join(Student).filter(Student.workspace_id == workspace_id).all()
    
    distribution = {
        "90-100": 0,
        "80-89": 0,
        "70-79": 0,
        "60-69": 0,
        "50-59": 0,
        "<50": 0
    }
    
    for r in results:
        avg = r.average_score
        if avg is None: continue
        
        if avg >= 90: distribution["90-100"] += 1
        elif avg >= 80: distribution["80-89"] += 1
        elif avg >= 70: distribution["70-79"] += 1
        elif avg >= 60: distribution["60-69"] += 1
        elif avg >= 50: distribution["50-59"] += 1
        else: distribution["<50"] += 1
        
    return {"distribution": distribution}

@router.get("/analytics/{workspace_id}/pass-fail")
def get_pass_fail_distribution(workspace_id: str, db: Session = Depends(get_db)):
    results = db.query(SemesterResult).join(Student).filter(Student.workspace_id == workspace_id).all()
    
    passed = sum(1 for r in results if r.status.upper() == "PASS")
    failed = len(results) - passed
    
    return {"passed": passed, "failed": failed}

@router.get("/analytics/{workspace_id}/gender-performance")
def get_gender_performance(workspace_id: str, db: Session = Depends(get_db)):
    results = db.query(SemesterResult, Student).join(Student).filter(Student.workspace_id == workspace_id).all()
    
    stats = {
        "Male": {"total_score": 0, "count": 0, "passed": 0},
        "Female": {"total_score": 0, "count": 0, "passed": 0}
    }
    
    for sem, student in results:
        gender = student.gender
        if not gender or gender.lower() not in ["male", "female", "m", "f", "boy", "girl"]:
            continue
            
        key = "Male" if gender.lower() in ["male", "m", "boy"] else "Female"
        
        stats[key]["count"] += 1
        if sem.average_score:
            stats[key]["total_score"] += sem.average_score
        if sem.status.upper() == "PASS":
            stats[key]["passed"] += 1
            
    final_stats = {}
    for g, s in stats.items():
        if s["count"] > 0:
            final_stats[g] = {
                "average": round(s["total_score"] / s["count"], 2),
                "pass_rate": round((s["passed"] / s["count"]) * 100, 1)
            }
        else:
            final_stats[g] = {"average": 0, "pass_rate": 0}
            
    return final_stats

@router.get("/analytics/{workspace_id}/insights")
def get_workspace_insights(workspace_id: str, db: Session = Depends(get_db)):
    if not groq_client:
        return {"insights": "Groq API key not configured. Cannot generate AI insights.", "attention_required": []}
        
    # Gather data for AI
    results = db.query(SemesterResult, Student).join(Student).filter(Student.workspace_id == workspace_id).all()
    if not results:
        return {"insights": "No data available yet.", "attention_required": []}
        
    total = len(results)
    passed = sum(1 for r, s in results if r.status.upper() == "PASS")
    failed = total - passed
    pass_rate = round((passed / total) * 100, 1) if total > 0 else 0
    
    attention_required = []
    for sem, student in results:
        if sem.status.upper() != "PASS":
            attention_required.append({
                "student": student.name,
                "register_number": student.register_number,
                "status": sem.status,
                "reason": "Failed one or more subjects",
                "average": sem.average_score
            })
            
    # Prepare prompt
    prompt = f"""
    You are an AI Academic Advisor analyzing a class's performance. Provide a short, insightful summary (2-3 sentences max) that a teacher would find useful.
    
    Data:
    Total Students: {total}
    Passed: {passed}
    Failed: {failed}
    Pass Rate: {pass_rate}%
    
    Focus on the overall health of the class, avoiding generic statements. Do not invent details like subject names if they aren't provided. Just summarize the numbers contextually.
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful academic AI assistant."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
            temperature=0.5,
            max_tokens=150
        )
        insight_text = chat_completion.choices[0].message.content
    except Exception as e:
        insight_text = f"Failed to generate insights: {str(e)}"
        
    return {
        "insights": insight_text,
        "attention_required": attention_required
    }

@router.get("/analytics/student/{student_id}")
def get_student_details(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    results = db.query(SemesterResult).filter(SemesterResult.student_id == student_id).all()
    
    semesters = []
    for sem in results:
        subjects = db.query(SubjectScore).filter(SubjectScore.semester_id == sem.id).all()
        semesters.append({
            "id": sem.id,
            "semester_number": sem.semester_number,
            "sgpa": sem.sgpa,
            "cgpa": sem.cgpa,
            "total_score": sem.total_score,
            "average_score": sem.average_score,
            "status": sem.status,
            "subjects": [
                {
                    "code": s.subject_code,
                    "name": s.subject_name,
                    "marks": s.total_marks,
                    "grade": s.grade,
                    "status": s.status
                }
                for s in subjects
            ]
        })
        
    return {
        "id": student.id,
        "register_number": student.register_number,
        "name": student.name,
        "gender": student.gender,
        "workspace_id": student.workspace_id,
        "semesters": semesters
    }