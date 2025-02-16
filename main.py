from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import requests
import os
from dotenv import load_dotenv
from controllers import user, gameAccount

load_dotenv()

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

app.include_router(user.user_router)
app.include_router(gameAccount.gameAccount_router)

api_key = os.getenv("RIOT_KEY")

class UserBase(BaseModel):
    email: str
    password: str

class RiotUserBase(BaseModel):
    user_id: int
    game_name: str
    tag_line: str
    summoner_id: str
    puuid: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# @app.post("/users/", status_code=status.HTTP_201_CREATED)
# async def create_user(user: UserBase, db: db_dependency):
#     db_user = models.User(**user.dict())
#     db.add(db_user)
#     db.commit()

# @app.get("/account/", status_code=status.HTTP_200_OK)
# async def get_account(tagline: str, gamename: str, db: db_dependency):
#     url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gamename}/{tagline}"
#     headers = {
#         'X-Riot-Token': api_key
#     }
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         riot_account = response.json()
#         if db.query(models.RiotUser).filter(models.RiotUser.puuid == riot_account['puuid']).first():
#             return riot_account
#         db_riot_user = models.RiotUser(game_name=riot_account['gameName'], tag_line=riot_account['tagLine'],  puuid=riot_account['puuid'])
#         db.add(db_riot_user)
#         db.commit()
#         return riot_account
#     else:
#         raise HTTPException(status_code=response.status_code, detail=response.json())