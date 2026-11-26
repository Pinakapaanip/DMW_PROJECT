from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import User
from app.library.schemas import CollectionCreateIn, SavePaperIn
from app.library.service import (
    create_collection,
    list_collections,
    list_library,
    remove_paper,
    save_paper,
)


router = APIRouter(prefix="/api/v1/library", tags=["Research library"])


@router.get("")
def get_library(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"papers": list_library(db, current_user.id)}


@router.post("/save", status_code=status.HTTP_201_CREATED)
def add_to_library(
    data: SavePaperIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        save_paper(db, current_user.id, data.paper_id.strip())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Paper saved to your library."}


@router.delete("/{paper_id}")
def delete_from_library(
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not remove_paper(db, current_user.id, paper_id):
        raise HTTPException(status_code=404, detail="Saved paper not found.")
    return {"message": "Paper removed from your library."}


@router.get("/collections")
def get_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"collections": list_collections(db, current_user.id)}


@router.post("/collections", status_code=status.HTTP_201_CREATED)
def add_collection(
    data: CollectionCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        collection = create_collection(db, current_user.id, data.name)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": collection.id,
        "name": collection.name,
        "paper_count": 0,
        "created_at": collection.created_at,
    }