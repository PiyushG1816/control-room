"""FastAPI application entrypoint for the Control Room backend."""

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes.runs import router as runs_router

app = FastAPI(title="Control Room")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Create all database tables on application startup."""
    Base.metadata.create_all(bind=engine)


app.include_router(runs_router)
