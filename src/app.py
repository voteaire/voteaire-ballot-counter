import newrelic.agent

newrelic.agent.initialize()

from distutils.log import debug
import os

from model import db
from model.proposal import Proposal
from model.question import Question
from model.choice import Choice
from model.vote import Vote
from model.vote_choice import VoteChoice
from model.processed_log import ProcessedLog
from model.blockfrost_queue import BlockfrostQueue

import logging
from flask_cors import CORS
import connexion
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import request
import sys
from dotenv import load_dotenv

load_dotenv()


LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
DB_CONN = os.environ.get("DB_CONN")

logging.basicConfig(level=LOGLEVEL, format="%(asctime)s %(levelname)s %(message)s")

logging.debug("nothing to see here...")
logging.info("informational")
logging.warning("something fishy")
logging.critical("holy crap batman!")

cors = CORS(supports_credentials=True)

options = {"swagger_ui": True}
conn = connexion.FlaskApp(__name__, specification_dir="openapi/", options=options)
conn.add_api("openapi-spec.yml", resolver_error=501)


app = conn.app


app.config["SQLALCHEMY_DATABASE_URI"] = DB_CONN
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db, compare_type=True)

with app.app_context():
    db.create_all()

cors.init_app(app)

application = app


if __name__ == "__main__":
    app.run(port=8081, debug=True)
