from lib import snapshotter_utils, blockchain_utils
from requests.exceptions import ConnectionError

import newrelic.agent
import logging


KUPO_URL = "http://kupo"
KUPO_PORT = 1442


class PolicyIdVoteWeighter(object):
    def vote_type(self):
        return "PolicyId"

    def vote_version(self):
        return "1.0.0"

    @newrelic.agent.background_task(name="policyid-weighter")
    def weight_vote(
        self,
        voter_stake_addr: str,
        snapshot_epoch: int,
        ballot_type: dict,
        chain_provider=None,
    ):

        if ballot_type["Name"] != self.vote_type():
            raise ValueError(
                f"Expected {self.vote_type()} ballot type, but received {ballot_type['Name']}"
            )

        # Get current slot
        # Ask for snapshot from user who created this vote for this snapshot slot

        # Find out snapshot time based on snapshot epoch
        snapshot_time = blockchain_utils.get_epoch_slot(snapshot_epoch, True)
        user_balance = snapshotter_utils.get_snapshot(
            KUPO_URL, KUPO_PORT, voter_stake_addr, snapshot_time
        )

        if user_balance is None:
            return {"status": "future-epoch"}

        weight = 0
        for asset, amount in user_balance["assets"].items():
            policy_id, _ = asset.split(".")

            if policy_id in ballot_type["PolicyId"]:
                weight += amount

        return {"status": "success", "vote_weight": weight}
