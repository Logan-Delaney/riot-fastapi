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
        return {
            'champ1': [getChamp(str(masteries[0]['championId'])), masteries[0]['championLevel']], 
            'champ2': [getChamp(str(masteries[1]['championId'])), masteries[1]['championLevel']],
            'champ3': [getChamp(str(masteries[2]['championId'])), masteries[2]['championLevel']]
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
@gameAccount_router.get("/ranked", status_code=status.HTTP_200_OK)
async def get_ranked(summoner_id: str, db: db_dependency):
    url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    headers = {
        'X-Riot-Token': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        ranked = response.json()
        if ranked[0]['queueType'] == 'RANKED_SOLO_5x5':
            solo_rank = ranked[0]['tier'] + " " + ranked[0]['rank']
            flex_rank = ranked[1]['tier'] + " " + ranked[1]['rank']
            solo_winrate = f"{round(ranked[0]['wins'] / (ranked[0]['wins'] + ranked[0]['losses']) * 100, 2)}%"
            flex_winrate = f"{round(ranked[1]['wins'] / (ranked[1]['wins'] + ranked[1]['losses']) * 100, 2)}%"
        else:
            solo_rank = ranked[1]['tier'] + " " + ranked[1]['rank']
            flex_rank = ranked[0]['tier'] + " " + ranked[0]['rank']
            solo_winrate = f"{round(ranked[1]['wins'] / (ranked[1]['wins'] + ranked[1]['losses']) * 100, 2)}%"
            flex_winrate = f"{round(ranked[0]['wins'] / (ranked[0]['wins'] + ranked[0]['losses']) * 100, 2)}%"
        user = db.query(models.RiotUser).filter(models.RiotUser.summoner_id == summoner_id).first()
        user.solo_rank = solo_rank
        user.flex_rank = flex_rank
        db.add(user)
        db.commit()
        return {
            "Solo_Duo": solo_rank,
            "Solo_Winrate": solo_winrate,
            "Flex": flex_rank,
            "Flex_Winrate": flex_winrate
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())

@gameAccount_router.get("/matches", status_code=status.HTTP_200_OK)
async def get_matches(puuid: str):
    count = 5
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    headers = {
        'X-Riot-Token': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        matches = response.json()
        all_matches = []
        for match in matches:
            match_url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match}"
            match_data = requests.get(match_url, headers=headers).json()
            particpants = match_data['info']['participants']
            for (index, participant) in enumerate(particpants):
                if participant['puuid'] == puuid:
                    this_match = {}
                    this_match['game_id'] = match_data['metadata']['matchId']
                    this_match['game_mode'] = match_data['info']['gameMode']
                    this_match['champion'] = match_data['info']['participants'][index]['championName']
                    this_match['kills'] = match_data['info']['participants'][index]['kills']
                    this_match['deaths'] = match_data['info']['participants'][index]['deaths']
                    this_match['assists'] = match_data['info']['participants'][index]['assists']
                    this_match['kda'] = f"{this_match['kills']}/{this_match['deaths']}/{this_match['assists']}"
                    this_match['win'] = match_data['info']['participants'][index]['win']
                    this_match['items'] = [match_data['info']['participants'][index]['item0'], match_data['info']['participants'][index]['item1'], match_data['info']['participants'][index]['item2'], match_data['info']['participants'][index]['item3'], match_data['info']['participants'][index]['item4'], match_data['info']['participants'][index]['item5'], match_data['info']['participants'][index]['item6']]
                    this_match['damage'] = match_data['info']['participants'][index]['totalDamageDealtToChampions']
                    this_match['gold'] = match_data['info']['participants'][index]['goldEarned']
                    this_match['cs'] = match_data['info']['participants'][index]['totalMinionsKilled']
                    all_matches.append(this_match)
        return all_matches
                    
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())

@gameAccount_router.get("/profile", status_code=status.HTTP_200_OK)
async def get_profile(tagline: str, gamename: str, db: db_dependency):
    riot_account = await get_account(tagline, gamename, db)
    puuid = riot_account['puuid']
    summoner_id = riot_account['summoner_id']
    mastery = await get_mastery(puuid, db)
    ranked = await get_ranked(summoner_id, db)
    matches = await get_matches(puuid)
    return {
        "riot_account":riot_account,
        "mastery": mastery, 
        "ranked": ranked, 
        "matches": matches
    }
    