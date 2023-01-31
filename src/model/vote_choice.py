import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import func

from . import db
from .vote import Vote


def str_uuid():
    return str(uuid.uuid4())


class VoteChoice(db.Model):
    __tablename__ = "vote_choice"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Auto Increment?
    vote_id = db.Column(db.Integer, ForeignKey("vote.id"), nullable=False)
    vote = relationship("Vote", back_populates="vote_choices")
    choice_id = db.Column(db.Integer, ForeignKey("choice.id"), nullable=False)
    choice = relationship("Choice")
    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )
