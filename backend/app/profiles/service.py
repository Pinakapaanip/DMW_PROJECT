from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Follow, ResearcherProfile, User


def serialize_profile(
    db: Session,
    user: User,
    viewer_id: int,
    include_private: bool = False,
) -> dict:
    profile = db.get(ResearcherProfile, user.id)
    following = db.scalar(
        select(Follow.follower_id).where(
            Follow.follower_id == viewer_id,
            Follow.followed_id == user.id,
        )
    ) is not None
    result = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "bio": user.bio,
        "institution": user.institution,
        "department": profile.department if profile else user.institution,
        "interests": profile.interests if profile else [],
        "role": user.role,
        "is_active": user.is_active,
        "is_following": following,
    }
    if include_private:
        result["email"] = user.email
    return result


def update_profile(db: Session, user: User, data) -> User:
    profile = db.get(ResearcherProfile, user.id)
    if profile is None:
        profile = ResearcherProfile(user_id=user.id)
        db.add(profile)
    user.full_name = data.full_name.strip()
    user.bio = data.bio.strip()
    profile.department = data.department.strip()
    profile.interests = [
        interest.strip()
        for interest in data.interests
        if interest.strip()
    ]
    db.commit()
    db.refresh(user)
    return user