from sqlalchemy import func
from . import db


class Config(db.Model):
    __tablename__ = "config"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    config_key = db.Column(db.String(), nullable=False)
    config_value = db.Column(db.String(), nullable=False)

    # str, int, json, datetime
    config_type = db.Column(db.String(), nullable=False)

    # caching interval in seconds
    caching_interval = db.Column(db.Integer, nullable=False)

    last_update_date = db.Column(
        db.DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
