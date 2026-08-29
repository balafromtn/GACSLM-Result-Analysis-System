from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.academic import Student, SemesterResult

router = APIRouter()

@router.get("/analytics/{workspace_id}/summary")
def get_workspace_summary(workspace_id: str, db: Session = Depends(get_db)):
    """
    Calculates the high-level metrics for the Next.js dashboard overview cards.
    """
    # 1. Verify workspace has students
    total_students = db.query(Student).filter(Student.workspace_id == workspace_id).count()
    if total_students == 0:
        raise HTTPException(status_code=404, detail="No students found in this workspace.")

    # 2. Get latest semester results for these students
    results = db.query(SemesterResult).join(Student).filter(Student.workspace_id == workspace_id).all()
    
    if not results:
        return {
            "total_students": total_students,
            "status": "Awaiting scraper completion..."
        }

    # 3. Calculate deterministic metrics
    total_passed = sum(1 for r in results if r.status.upper() == "PASS")
    total_failed = sum(1 for r in results if r.status.upper() != "PASS")
    
    # Calculate average SGPA (ignoring None values)
    valid_sgpas = [r.sgpa for r in results if r.sgpa is not None]
    avg_sgpa = round(sum(valid_sgpas) / len(valid_sgpas), 2) if valid_sgpas else 0.0

    return {
        "workspace_id": workspace_id,
        "total_students": total_students,
        "metrics": {
            "passed": total_passed,
            "failed": total_failed,
            "pass_percentage": round((total_passed / total_students) * 100, 1) if total_students > 0 else 0,
            "average_sgpa": avg_sgpa
        }
    }