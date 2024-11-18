from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    name = Column(String, nullable=True)
    score = Column(Integer, nullable=False)

    participants = relationship("ParticipantModel", cascade="all, delete-orphan", backref="user", passive_deletes=True)

class ChatModel(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    game_time = Column(Integer, nullable=False)
    answer_time = Column(Integer, nullable=False)

    games = relationship("GameModel", cascade="all, delete-orphan", backref="user", passive_deletes=True)
