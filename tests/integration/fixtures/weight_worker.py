import threading
import importlib
import pytest
import sys
import os

from flask import Flask
from flask_migrate import Migrate


@pytest.fixture
def weight_worker():
    sys.path.append("src")

    from workers.weight import run_weight_worker

    from model import db
    from model.proposal import Proposal
    from model.question import Question
    from model.choice import Choice
    from model.vote import Vote
    from model.vote_choice import VoteChoice
    from model.processed_log import ProcessedLog
    from model.blockfrost_queue import BlockfrostQueue

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        db.create_all()

    provider = os.environ.get("CHAIN_PROVIDER", "blockfrost")
    chain_prov = importlib.import_module(f"meta.chain_providers.{provider}")

    def worker():
        with app.app_context():
            run_weight_worker(db.session, chain_prov, delay=0.1)

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

    with app.app_context():
        yield db.session
