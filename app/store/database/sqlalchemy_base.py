from sqlalchemy import (
    BOOLEAN,
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    Nullable,
    Sequence,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import BOOLEANTYPE, TIMESTAMP

Base = declarative_base()

class ThemeModel(Base):
    __tablename__ = "themes"
    id = Column(Integer, Sequence("themes_id_seq", start=1), primary_key=True)
    title = Column(String, nullable=False, unique=True)

    questions = relationship("QuestionModel", cascade="all, delete-orphan", backref="themes", passive_deletes=True)
    games = relationship("GameModel", backref="themes",)


class QuestionModel(Base):
    __tablename__ = "questions"
    id = Column(Integer, Sequence("questions_id_seq", start=1), primary_key=True)
    title = Column(String, nullable=False, unique=True)
    theme_id = Column(Integer, ForeignKey('themes.id', ondelete='CASCADE'), nullable=False)

    answers = relationship("AnswerModel", cascade="all, delete-orphan",  backref="questions", passive_deletes=True)

class AnswerModel(Base):
    __tablename__ = "answers"
    id = Column(Integer, Sequence("answers_id_seq", start=1), primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=False)
    is_correct = Column(BOOLEANTYPE, nullable=False)

class GameModel(Base):
    __tablename__ = "games"
    id = Column(Integer, Sequence("games_id_seq", start=1), primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    theme_id = Column(Integer, ForeignKey('themes.id', ondelete='CASCADE'), nullable=True)
    answer_time = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    ended_at = Column(TIMESTAMP, nullable=True)
    state = Column(String, nullable=False)
    current_question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), nullable=True)

    participants = relationship("ParticipantModel", cascade="all, delete-orphan", backref="games", passive_deletes=True)
    game_questions = relationship("GameQuestionModel", cascade="all, delete-orphan", backref="games", passive_deletes=True)


class GameQuestionModel(Base):
    __tablename__ = "game_questions"
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True)

class ParticipantModel(Base):
    __tablename__ = "participants"
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    level = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False, default=0)
    incorrect_answers = Column(Integer, nullable=False, default=0)
    current = Column(BOOLEAN, nullable=False)


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, Sequence("users_id_seq", start=1), primary_key=True)
    username = Column(String, nullable=True)
    name = Column(String, nullable=True)
    score = Column(Integer, nullable=False)

class ChatModel(Base):
    __tablename__ = "chats"
    id = Column(BigInteger, primary_key=True)

    games = relationship("GameModel", cascade="all, delete-orphan", backref="chats", passive_deletes=True)

class UpdateModel(Base):
    __tablename__ = "updates"
    offset = Column(BigInteger, primary_key=True)
