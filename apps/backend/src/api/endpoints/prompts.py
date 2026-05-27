# =============================================================================
# IELTS Prompt Endpoints
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database import IELTSPrompt, get_db

router = APIRouter()


@router.get("/prompts/random")
def get_random_prompt(db: Session = Depends(get_db)):
    """Return one random IELTS Speaking prompt from the database."""
    prompt = db.query(IELTSPrompt).order_by(func.random()).first()

    if prompt is None:
        raise HTTPException(
            status_code=404,
            detail="No IELTS prompts found. Run the seed script first.",
        )

    return {
        "id": prompt.id,
        "part": prompt.part,
        "topic": prompt.topic,
        "question": prompt.question,
    }
