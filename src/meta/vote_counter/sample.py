class SampleVoteCounter:
    def __init__(self):
        pass

    def vote_type(self):
        return "Sample"

    def process_vote(self, tx_hash, metadata, proposal, chain_provider):
        """Counts a simple vote

        Parameters:
        tx_hash: the transaction hash
        metadata: metadata of the vote
        chain_provider: a provider for on-chain data

        Returns:
        object:
            status: bool
            errors: optional array of strings
            results: the vote result in json format

        """
        # lookup extra info we need orm the chain
        return {"tx_hash": "SAMPLE"}
