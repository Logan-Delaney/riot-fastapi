from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import requests
import os
from dotenv import load_dotenv

user_router = APIRouter(
    prefix="/user",
    tags=["user"]
)

api_key = os.getenv("RIOT_KEY")

class UserBase(BaseModel):
    email: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@user_router.post("/create/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserBase, db: db_dependency):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()