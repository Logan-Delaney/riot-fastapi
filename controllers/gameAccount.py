from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import requests
import os
from dotenv import load_dotenv
from utils.getChamp import getChamp

load_dotenv()

gameAccount_router = APIRouter(
    prefix="/game-account",
    tags=["game-account"]
)

api_key = os.getenv("RIOT_KEY")

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

@gameAccount_router.get("", status_code=status.HTTP_200_OK)
async def get_account(tagline: str, gamename: str, db: db_dependency):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gamename}/{tagline}"
    headers = {
        'X-Riot-Token': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        riot_account = response.json()
        puuid = riot_account['puuid']
        summoner_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        summoner_account = requests.get(summoner_url, headers=headers).json()
        riot_account['summoner_id'] = summoner_account['id']
        if db.query(models.RiotUser).filter(models.RiotUser.puuid == riot_account['puuid']).first():
            return riot_account
        db_riot_user = models.RiotUser(game_name=riot_account['gameName'], tag_line=riot_account['tagLine'],  puuid=riot_account['puuid'], summoner_id=riot_account['summoner_id'])
        db.add(db_riot_user)
        db.commit()
        return riot_account
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
@gameAccount_router.get("/champion", status_code=status.HTTP_200_OK)
async def get_champion(champ_id: str):
    return getChamp(champ_id)

@gameAccount_router.get("/mastery", status_code=status.HTTP_200_OK)
async def get_mastery(puuid: str, db: db_dependency):
    url = f"https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=3"
    headers = {
        'X-Riot-Token': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        masteries = response.json()
        return getChamp(str(masteries[0]['championId'])), getChamp(str(masteries[1]['championId'])), getChamp(str(masteries[2]['championId']))
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())