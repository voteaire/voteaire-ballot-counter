import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy import func

from . import db
from .vote_choice import VoteChoice


def str_uuid():
    return str(uuid.uuid4())


class Choice(db.Model):
    __tablename__ = "choice"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    choice_identifier = db.Column(db.String, default=str_uuid, index=True)
    question_id = db.Column(db.Integer, ForeignKey("question.id"), nullable=False, index=True)
    question = relationship("Question", back_populates="choices")
    choice = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    vote_choices = relationship("VoteChoice", back_populates="choice")

    # Maybe remove this since it's created at the same time as proposal
    created_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )
