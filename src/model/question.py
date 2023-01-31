import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy import func

from . import db


def str_uuid():
    return str(uuid.uuid4())


class Question(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_identifier = db.Column(db.String, default=str_uuid, index=True)
    proposal_id = db.Column(db.Integer, ForeignKey("proposal.id"), index=True)
    proposal = relationship("Proposal", back_populates="questions")
    question = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    choice_limit = db.Column(db.Integer, nullable=False)
    choices = relationship("Choice", back_populates="question")

    # Maybe remove this since it's created at the same time as proposal
    created_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )
