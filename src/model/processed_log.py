import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy import func

from . import db
from .vote_choice import VoteChoice


class ProcessedLog(db.Model):
    __tablename__ = "processed_log"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tx_hash = db.Column(db.String, nullable=False, index=True)
    valid = db.Column(db.Boolean, nullable=False)
    success = db.Column(db.Boolean, nullable=True)
    details = db.Column(db.String)
    tx_metadata = db.Column(db.JSON, nullable=False)
    tx_block_height = db.Column(db.Integer, nullable=True)
    tx_datetime = db.Column(db.DateTime(timezone=False), nullable=True)
    vote_id = db.Column(db.Integer, ForeignKey("vote.id"), nullable=True)
    proposal_id = db.Column(db.Integer, ForeignKey("proposal.id"), nullable=True)
    created_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )
