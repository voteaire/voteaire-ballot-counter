import os
import pytest
import dotenv
import sys

from flask import Flask
from flask_migrate import Migrate


dotenv.load_dotenv()

DB_URL = os.getenv("DB_CONN")
if DB_URL is None:
    raise ValueError("Undefined DB_CONN!")


@pytest.fixture(scope="class")
def session():

    sys.path.append("src")

    from model import db
    from model.proposal import Proposal
    from model.question import Question
    from model.choice import Choice
    from model.vote import Vote
    from model.vote_choice import VoteChoice
    from model.processed_log import ProcessedLog
    from model.blockfrost_queue import BlockfrostQueue

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        db.create_all()
        yield db.session
