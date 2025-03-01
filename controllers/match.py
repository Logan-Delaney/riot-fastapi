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

load_dotenv(override=True)

match_router = APIRouter(
    prefix="/match",
    tags=["match"]
)

api_key = os.getenv("RIOT_KEY")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@match_router.get("/match-detail", status_code=status.HTTP_200_OK)
async def get_matches(puuid: str, match_id: str, db: db_dependency):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {
        'X-Riot-Token': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        match = response.json()
        participants = match['info']['participants']
        summoner_list = []
        for participant in participants:
            if participant['puuid'] == puuid:
                summoner = db.query(models.RiotUser).filter(models.RiotUser.puuid == participant['puuid']).first()
                summoner_list.append(summoner.game_name)
            else:
                game_name_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-puuid/{participant['puuid']}"
                summoner = requests.get(game_name_url, headers=headers).json()
                summoner_list.append(summoner['gameName'])
        return {
            'summoners': summoner_list, 
            'match': match}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())

