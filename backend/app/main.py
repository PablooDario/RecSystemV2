from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import movie_router, user_router, registration_router, auth_router, rating_router, recommendation_router, watchlist_router, personality_router, survey_router
from app.services.recommendations.model_loader import load_all_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all_models()
    yield


app = FastAPI(
    title="Movie API",
    description="API to handle users, movies, and ratings",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movie_router)
app.include_router(user_router)
app.include_router(registration_router)
app.include_router(auth_router)
app.include_router(rating_router)
app.include_router(recommendation_router)
app.include_router(watchlist_router)
app.include_router(personality_router)
app.include_router(survey_router)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Movie API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

# uvicorn app.main:app --reload  