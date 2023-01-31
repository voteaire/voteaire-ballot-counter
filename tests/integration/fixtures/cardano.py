import pytest
import connexion
import sys


class Cardano(object):
    def create_proposal_transaction(self):
        pass

    def create_vote_transaction(self):
        pass

    def create_invalid_transaction(self):
        pass

    def sign_transaction(self):
        pass

    def submit_transaction(self):
        pass


@pytest.fixture(scope="class")
def cardano():

    sys.path.append("src")

    pass
