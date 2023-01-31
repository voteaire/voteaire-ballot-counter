import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import func

from . import db


def str_uuid():
    return str(uuid.uuid4())


class BlockfrostQueue(db.Model):
    __tablename__ = "blockfrost_queue"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    page = db.Column(db.Integer, nullable=False)
    index = db.Column(db.Integer, nullable=False)
    tx_hash = db.Column(db.String, nullable=False)
    json_metadata = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String, default="queued", nullable=False)  # queued, processed
    insertion_date = db.Column(
        db.DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    processed_date = db.Column(db.DateTime(timezone=False))
