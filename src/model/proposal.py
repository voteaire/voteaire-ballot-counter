from time import timezone
import uuid

from sqlalchemy.orm import relationship

# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func

from . import db


def str_uuid():
    return str(uuid.uuid4())


class Proposal(db.Model):
    __tablename__ = "proposal"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    proposal_identifier = db.Column(db.String(64), default=str_uuid, index=True )
    version = db.Column(db.String(64), nullable=False)
    network_id = db.Column(db.String(64), nullable=False)
    proposal_url = db.Column(db.String(64))
    creator_stake_address = db.Column(db.String(64), index=True )
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String())
    # Simple, Delegated, PolicyId
    ballot_type = db.Column(db.String(64), nullable=False)
    snapshot_epoch = db.Column(db.Integer, nullable=False)
    pool_id = db.Column(db.String)
    policy_id = db.Column(db.String)  # TODO: Should be array
    # draft, submitted, on-chain
    status = db.Column(db.String(64), default="draft", nullable=False, index=True )
    questions = relationship("Question", back_populates="proposal")
    tx_hash = db.Column(db.String())
    proposal_metadata = db.Column(db.String())
    source = db.Column(db.String())  # (frontend or manual)
    votes = relationship("Vote", back_populates="proposal")
    start_epoch = db.Column(db.Integer, nullable=False, index=True )
    end_epoch = db.Column(db.Integer, nullable=False, index=True )
    creation_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    submitted_date = db.Column(db.DateTime(timezone=False))
    # Date proposal was found onchain
    processed_date = db.Column(db.DateTime(timezone=False))
    # Date of the block creation in which this proposal is
    onchain_date = db.Column(db.DateTime(timezone=False))

    # def __repr__(self):
    #     # TODO: Update this
    #     args = [
    #         f"id={self.id!r}",
    #         f"creator_address={self.creator_address!r}",
    #         f"title={self.title!r}",
    #         f"vote_type={self.vote_type!r}",
    #         f"snapshot_epoch={self.snapshot_epoch!r}",
    #         f"pool_id={self.pool_id!r}",
    #         f"policy_id={self.policy_id!r}",
    #         f"questions={self.questions!r}",
    #         f"start_date={self.start_date!r}",
    #         f"end_date={self.end_date!r}",
    #         f"creation_date={self.creation_date!r}"
    #     ]

    #     return f"User({', '.join(args)})"
