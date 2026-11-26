
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import Base, engine
from app.database import models

from app.auth.routes import router as auth_router
from app.analytics.routes import router as analytics_router
from app.assistant.routes import router as assistant_router
from app.ingestion.routes import router as ingestion_router
from app.library.routes import router as library_router
from app.posts.routes import router as posts_router
from app.profiles.routes import router as profiles_router
from app.recommendations.routes import router as recommendations_router
from app.search.routes import router as search_router
from app.trends.routes import router as trends_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title="Chanakya Research Commons API",
    description="Research collaboration and knowledge-sharing platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(posts_router)
app.include_router(library_router)
app.include_router(ingestion_router)
app.include_router(search_router)
app.include_router(recommendations_router)
app.include_router(trends_router)
app.include_router(assistant_router)
app.include_router(analytics_router)


@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "message": "Backend is running"
    }
