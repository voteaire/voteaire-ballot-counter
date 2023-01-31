import newrelic.agent


class DelegatedVoteWeighter(object):
    def vote_type(self):
        return "Delegated"

    def vote_version(self):
        return "1.0.0"

    @newrelic.agent.background_task(name="delegated-weighter")
    def weight_vote(
        self,
        voter_stake_addr: str,
        snapshot_epoch: int,
        ballot_type: dict,
        chain_provider,
    ):
        # TODO: pass both chain and snapshot provider and allow them to be None

        # provider could be either chain provider or snapshotter provider???
        # or should snapshoter provider be abstract enough to get ADA snapshots too?

        # Assume the ballot metadata is valid??

        if ballot_type["Name"] != self.vote_type():
            raise ValueError(
                f"Expected {self.vote_type()} ballot type, but received {ballot_type['Name']}"
            )

        current_epoch = int(chain_provider.get_current_epoch()["epoch"])

        if snapshot_epoch > current_epoch:
            return {"status": "future-epoch"}

        epoch_stake_snapshot = chain_provider.get_epoch_snapshot(
            voter_stake_addr, snapshot_epoch
        )

        if epoch_stake_snapshot is None:
            return {
                "status": "invalid",
                "message": "User did not have registered delegation before the snapshot! Epoch snapshot not found!",
            }

        if epoch_stake_snapshot["pool_id"] != ballot_type["PoolId"]:
            return {
                "status": "invalid",
                "message": f"User did not delegate to right pool. Expected {ballot_type['PoolId']} but got {epoch_stake_snapshot['pool_id']}",
            }

        snapshot_balance = int(epoch_stake_snapshot["amount"])

        return {"status": "success", "vote_weight": snapshot_balance}
