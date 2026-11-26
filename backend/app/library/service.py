from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database.models import (
    LibraryCollection,
    LibraryItem,
    ResearchPaper,
)
from app.ingestion.storage import paper_to_dict


def list_library(db: Session, user_id: int) -> list[dict]:
    items = db.scalars(
        select(LibraryItem)
        .options(selectinload(LibraryItem.paper))
        .where(LibraryItem.user_id == user_id)
        .order_by(LibraryItem.created_at.desc())
    ).all()
    return [
        {
            **paper_to_dict(item.paper),
            "saved_at": item.created_at,
        }
        for item in items
    ]


def save_paper(db: Session, user_id: int, paper_id: str) -> None:
    if db.get(ResearchPaper, paper_id) is None:
        raise LookupError("Research paper not found.")
    if db.get(LibraryItem, (user_id, paper_id)) is None:
        db.add(LibraryItem(user_id=user_id, paper_id=paper_id))
        db.commit()


def remove_paper(db: Session, user_id: int, paper_id: str) -> bool:
    item = db.get(LibraryItem, (user_id, paper_id))
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True


def list_collections(db: Session, user_id: int) -> list[dict]:
    collections = db.scalars(
        select(LibraryCollection)
        .where(LibraryCollection.user_id == user_id)
        .order_by(LibraryCollection.created_at.desc())
    ).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "paper_count": 0,
            "created_at": item.created_at,
        }
        for item in collections
    ]


def create_collection(
    db: Session,
    user_id: int,
    name: str,
) -> LibraryCollection:
    normalized_name = name.strip()
    existing = db.scalar(
        select(LibraryCollection).where(
            LibraryCollection.user_id == user_id,
            func.lower(LibraryCollection.name) == normalized_name.lower(),
        )
    )
    if existing is not None:
        raise FileExistsError("A collection with that name already exists.")
    collection = LibraryCollection(user_id=user_id, name=normalized_name)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection