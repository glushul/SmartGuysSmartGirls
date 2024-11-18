from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import Base


class GameModel(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    theme_id = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    ended_at = Column(TIMESTAMP, nullable=False)

    participants = relationship("ParticipantModel", cascade="all, delete-orphan", backref="game", passive_deletes=True)
    game_questions = relationship("GameQuestionModel", cascade="all, delete-orphan", backref="game", passive_deletes=True)


class GameQuestionModel(Base):
    __tablename__ = "game_questions"
    game_id = Column(Integer, primary_key=True)
    question_id = Column(Integer, primary_key=True)

class ParticipantModel(Base):
    __tablename__ = "games"
    game_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    level = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    incorrect_answers = Column(Integer, nullable=False)
