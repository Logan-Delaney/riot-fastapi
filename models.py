from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(25))
    
class RiotUser(Base):
    __tablename__ = "riot_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_name = Column(String(50))
    tag_line = Column(String(10))
    summoner_id = Column(String(64))
    puuid = Column(String(100))