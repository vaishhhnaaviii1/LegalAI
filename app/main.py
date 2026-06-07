from fastapi import FastAPI

from app.db.database import create_db_and_tables

from app.routes.user_routes import router as user_router
from app.routes.case_routes import router as case_router
from app.routes import ipc_routes

import app.models


app = FastAPI()

app.include_router(user_router)
app.include_router(case_router)
app.include_router(
    ipc_routes.router
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def home():
    return {
        "message": "LegalAI Running"
    }