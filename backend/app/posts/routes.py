from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import Post, PostComment, User
from app.posts.schemas import CommentCreate, PostCreate
from app.posts.service import (
    add_comment,
    create_post,
    list_posts,
    serialize_post,
    toggle_upvote,
)


router = APIRouter(tags=["F2 Community posts"])


@router.get("/api/v1/feed")
def feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"posts": list_posts(db, current_user)}


@router.get("/api/v1/posts")
def posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"items": list_posts(db, current_user)}


@router.post("/api/v1/posts", status_code=status.HTTP_201_CREATED)
def publish_post(
    data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = create_post(db, current_user, data.body, data.tags)
    post = db.scalars(
        select(Post)
        .options(
            selectinload(Post.author),
            selectinload(Post.comments).selectinload(PostComment.author),
            selectinload(Post.votes),
        )
        .where(Post.id == post.id)
    ).one()
    return serialize_post(db, post, current_user.id)


@router.post("/api/v1/posts/{post_id}/upvote")
def upvote_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {"upvoted": toggle_upvote(db, post, current_user)}


@router.post(
    "/api/v1/posts/{post_id}/comments",
    status_code=status.HTTP_201_CREATED,
)
def comment_on_post(
    post_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    comment = add_comment(db, post, current_user, data.body)
    return {
        "id": comment.id,
        "body": comment.body,
        "created_at": comment.created_at,
        "author": {
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "bio": current_user.bio,
            "role": current_user.role,
        },
    }