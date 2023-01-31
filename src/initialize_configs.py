#!/bin/bash

import logging
import os

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

from workers import chain

from flask import Flask
from flask_migrate import Migrate

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from meta.metadata_processor import MetadataProcessor

# app setup
load_dotenv()

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
        keys = []
        while True:
            answer = input("Want to initialize config keys? (Y, n)")
            if answer.lower() == "y":
                config_utils.insert_config("simple_fees", 10_000_000, "int", 30)
                config_utils.insert_config("delegated_fees", 20_000_000, "int", 30)
                config_utils.insert_config("policyid_fees", 30_000_000, "int", 30)

            config_key = input("Config Key Name [ENTER to stop]: ")
            if config_key == "":
                break

            config_value = input("Config Value: ")
            if config_value == "":
                break

            config_type = input("Config Type (str, int, json, datetime): ")
            if config_type == "":
                break

            caching_interval = int(input("Caching Interval: "))
            if config_type == "":
                break

            config_utils.insert_config(
                config_key, config_value, config_type, caching_interval
            )
            keys.append(config_key)

        if len(keys) > 0:
            print(f"Awesome! Added {len(keys)} more config entries: {', '.join(keys)}")
        else:
            print("Added no config entries :/")


if __name__ == "__main__":
    main()
