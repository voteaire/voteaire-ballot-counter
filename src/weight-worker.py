#!/bin/bash

import newrelic.agent

newrelic.agent.initialize()
application = newrelic.agent.register_application(timeout=10.0)

import json
import logging
import re
import os
import importlib
import atexit

from time import sleep

from dotenv import load_dotenv

from model import db
from model.proposal import Proposal
from model.question import Question
from model.choice import Choice
from model.vote import Vote
from model.vote_choice import VoteChoice
from model.processed_log import ProcessedLog
from model.blockfrost_queue import BlockfrostQueue

from lib import config_utils

from meta.vote_weighter import VoteWeighter

from workers import weight

from flask import Flask
from flask_migrate import Migrate

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from meta.metadata_processor import MetadataProcessor

# app setup
load_dotenv()

# Setup Logging
LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()

# LOGLEVEL not working for some reason
logging.basicConfig(
    level=LOGLEVEL, format="%(asctime)s %(levelname)s %(message)s", force=True
)
logging.getLogger().setLevel(LOGLEVEL)
logging.info("Worker Starting...")

# Setup chain provider
provider = os.environ.get("CHAIN_PROVIDER", "blockfrost")
chain_prov = importlib.import_module(f"meta.chain_providers.{provider}")
logging.info(f"Setting up chain - {provider}")


# Setup queue provider
provider = os.environ.get("QUEUE_PROVIDER", "sqs")
queue_prov_class = getattr(
    importlib.import_module(f"meta.queue_providers.{provider}_queue_provider"),
    f"{provider.capitalize()}QueueProvider",
)
queue_prov = queue_prov_class()
logging.info(f"Setting up queue - {provider}")

# Setup db
DB_CONN = os.environ.get("DB_CONN")

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = DB_CONN
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


def main():
    with app.app_context():
        config_utils.wait_for_configs()

        weight.run_weight_worker(db.session, chain_prov, 10)


if __name__ == "__main__":
    main()
