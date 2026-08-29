from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.academic import Workspace
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

    required_cols = {"reg_no", "dob", "gender"}
    actual_cols = set(df.columns)
    if not required_cols.issubset(actual_cols):
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required columns. Must contain: {required_cols}. Found: {actual_cols}"
        )

    workspace = Workspace(name=workspace_name, owner_id="test_tutor_123")
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    records = df.to_dict(orient="records")
    
    # <-- TRIGGER THE BACKGROUND SCRAPER HERE -->
    background_tasks.add_task(process_student_batch, workspace.id, records, db)
    
    return {
        "status": "success",
        "message": f"Successfully queued {len(records)} students for scraping.",
        "workspace_id": workspace.id
    }