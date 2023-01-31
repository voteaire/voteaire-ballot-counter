import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import func

from . import db


def str_uuid():
    return str(uuid.uuid4())


class Vote(db.Model):
    __tablename__ = "vote"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vote_identifier = db.Column(db.String(64), default=str_uuid, index=True)
    proposal_id = db.Column(db.Integer, ForeignKey("proposal.id"), nullable=False, index=True)
    proposal = relationship("Proposal", back_populates="votes")
    vote_choices = relationship("VoteChoice", back_populates="vote")
    version = db.Column(db.String(64), nullable=False)
    voter_stake_address = db.Column(db.String(64), nullable=False, index=True)
    # should be assigned once the vote is on-chain
    weight = db.Column(db.Numeric(20).with_variant(db.BigInteger, "sqlite"))
    # draft, submitted, on-chain, weighted
    status = db.Column(db.String(64), default="draft", nullable=False, index=True)
    tx_hash = db.Column(db.String())
    vote_metadata = db.Column(db.String())
    source = db.Column(db.String())  # (frontend or manual)
    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    submitted_date = db.Column(db.DateTime(timezone=False))
    # Date vote was found onchain
    processed_date = db.Column(db.DateTime(timezone=False))
    # Date of the block creation in which this vote is
    onchain_date = db.Column(db.DateTime(timezone=False))
