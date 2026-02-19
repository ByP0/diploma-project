from fastapi import FastAPI
from app.api.auth import router as auth_router

app = FastAPI(title="API")

app.include_router(auth_router)
