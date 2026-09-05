from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.academic import Workspace, Student
from app.services.scraper_task import process_student_batch # <-- Import the new task
import pandas as pd
import io

router = APIRouter()

@router.post("/upload")
async def upload_student_data(
    workspace_name: str, 
    background_tasks: BackgroundTasks, # <-- Inject BackgroundTasks
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV or XLSX files are allowed.")

    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    required_cols = {"reg_no", "dob", "gender", "community"}
    actual_cols = set(df.columns)
    if not required_cols.issubset(actual_cols):
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required columns. Must contain: {required_cols}. Found: {actual_cols}"
        )

    # Use the deterministic workspace_name as the workspace_key
    workspace_key = workspace_name
    workspace = db.query(Workspace).filter(Workspace.workspace_key == workspace_key).first()
    if not workspace:
        workspace = Workspace(name=workspace_key, workspace_key=workspace_key, owner_id="test_tutor_123")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

    records = df.to_dict(orient="records")
    
    # <-- TRIGGER THE BACKGROUND SCRAPER HERE -->
    background_tasks.add_task(process_student_batch, workspace.id, records)
    
    return {
        "status": "success",
        "message": f"Successfully queued {len(records)} students for scraping.",
        "workspace_id": workspace.id
    }

@router.get("/workspace/{workspace_id}/status")
def get_scraping_status(workspace_id: str, db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.workspace_id == workspace_id).all()
    
    status_list = []
    for s in students:
        status_list.append({
            "register_number": s.register_number,
            "status": s.scraping_status,
            "error": s.scraping_error
        })
        
    return {"students": status_list}