from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import Follow, User
from app.profiles.schemas import ProfileUpdate
from app.profiles.service import serialize_profile, update_profile


router = APIRouter(prefix="/api/v1/users", tags=["F3 Researcher profiles"])


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = db.scalars(
        select(User).where(User.is_active.is_(True)).order_by(User.username)
    ).all()
    return {
        "users": [
            serialize_profile(db, user, current_user.id)
            for user in users
        ]
    }


@router.get("/me")
def read_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return serialize_profile(db, current_user, current_user.id, include_private=True)


@router.put("/me")
def edit_my_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = update_profile(db, current_user, data)
    return serialize_profile(db, user, user.id, include_private=True)


@router.get("/{user_id}")
def read_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=404, detail="Researcher not found.")
    return serialize_profile(db, user, current_user.id)


@router.post("/{user_id}/follow", status_code=status.HTTP_200_OK)
def follow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")
    followed = db.get(User, user_id)
    if followed is None or not followed.is_active:
        raise HTTPException(status_code=404, detail="Researcher not found.")
    if db.get(Follow, (current_user.id, user_id)) is None:
        db.add(Follow(follower_id=current_user.id, followed_id=user_id))
        db.commit()
    return {"following": True}


@router.delete("/{user_id}/follow")
def unfollow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follow = db.get(Follow, (current_user.id, user_id))
    if follow is not None:
        db.delete(follow)
        db.commit()
    return {"following": False}