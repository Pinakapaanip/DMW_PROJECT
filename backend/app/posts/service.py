from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.models import Post, PostComment, PostVote, User
from app.profiles.service import serialize_profile


def _serialize_comment(db: Session, comment: PostComment) -> dict:
    return {
        "id": comment.id,
        "body": comment.body,
        "created_at": comment.created_at,
        "author": serialize_profile(db, comment.author, comment.author_id),
    }


def serialize_post(
    db: Session,
    post: Post,
    viewer_id: int,
) -> dict:
    return {
        "id": post.id,
        "body": post.body,
        "tags": post.tags or [],
        "created_at": post.created_at,
        "author": serialize_profile(db, post.author, post.author_id),
        "comments": [
            _serialize_comment(db, comment)
            for comment in post.comments
        ],
        "comments_count": len(post.comments),
        "upvotes_count": len(post.votes),
        "is_upvoted": any(vote.user_id == viewer_id for vote in post.votes),
    }


def list_posts(db: Session, viewer: User) -> list[dict]:
    posts = db.scalars(
        select(Post)
        .options(
            selectinload(Post.author),
            selectinload(Post.comments).selectinload(PostComment.author),
            selectinload(Post.votes),
        )
        .order_by(Post.created_at.desc(), Post.id.desc())
    ).unique().all()
    return [serialize_post(db, post, viewer.id) for post in posts]


def create_post(db: Session, author: User, body: str, tags: list[str]) -> Post:
    post = Post(
        author_id=author.id,
        body=body.strip(),
        tags=[tag.strip().lstrip("#") for tag in tags if tag.strip()],
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def add_comment(
    db: Session,
    post: Post,
    author: User,
    body: str,
) -> PostComment:
    comment = PostComment(
        post_id=post.id,
        author_id=author.id,
        body=body.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def toggle_upvote(db: Session, post: Post, user: User) -> bool:
    vote = db.get(PostVote, (post.id, user.id))
    if vote is None:
        db.add(PostVote(post_id=post.id, user_id=user.id))
        db.commit()
        return True
    db.delete(vote)
    db.commit()
    return False