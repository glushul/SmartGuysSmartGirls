from sqlalchemy import Column, VARCHAR, BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql.sqltypes import BOOLEANTYPE

from app.store.database.sqlalchemy_base import Base


class ThemeModel(Base):
    __tablename__ = "themes"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)

    questions = relationship("QuestionModel", cascade="all, delete-orphan", backref="theme", passive_deletes=True)
    games = relationship("GameModel", cascade="all, delete-orphan", backref="theme", passive_deletes=True)


class QuestionModel(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    theme_id = Column(Integer, ForeignKey('themes.id', ondelete='CASCADE'), nullable=False)

    answers = relationship("AnswerModel", cascade="all, delete-orphan",  backref="question", passive_deletes=True)
    game_questions = relationship("GameQuestionModel", cascade="all, delete-orphan",  backref="question", passive_deletes=True)

class AnswerModel(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=False)
    is_correct = Column(BOOLEANTYPE, nullable=False)