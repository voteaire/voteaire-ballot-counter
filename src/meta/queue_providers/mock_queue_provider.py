import json

#  a queue provider should implement 2 methods, next() and ack()
# next will provide the next record to process, or None if there are none
# records are {tx_hash: hash, metadata: {...}}


class MockQueueProvider:
    def __init__(self):
        self.returnvals = [
            {
                "ObjectType": "BallotProposal",
                "ObjectVersion": "1.0.0",
                "NetworkId": "Voteaire",
                "ProposalId": "52da18fb-64ec-4d00-9484-fdb0b67ef678",
                "ProposalURL": "https://canucks-publishing.com",
                "BallotType": {"Name": "Simple"},
                "Title": "Pineapple on pizza?",
                "Questions": [
                    {
                        "QuestionId": "36f06c15-5a2d-4c7c-bf56-ffb2affb8320",
                        "Question": [
                            "Do you think people should be allowed to put pineapple on pizza?"
                        ],
                        "Description": [
                            "People have been putting odd things on pizza for centuries, however ",
                            "pineapple is a particularly polarizing topping.",
                        ],
                        "ChoiceLimit": 1,
                        "Choices": [
                            {
                                "ChoiceId": "c17d31d5-3bea-41b9-91fc-e9adba00daee",
                                "Name": "Hell yeah, pineapple is great!",
                                "Description": [],
                            },
                            {
                                "ChoiceId": "b0fbc41a-13ff-415f-8516-defef00b6980",
                                "Name": "Are you crazy? No way!",
                                "Description": [],
                            },
                        ],
                    }
                ],
                "VoteStartEpoch": 329,
                "VoteEndEpoch": 329,
                "SnapshotEpoch": 328,
            },
            {
                "ObjectType": "VoteBallot",
                "ObjectVersion": "1.0.0",
                "VoteId": "c9491488-9176-4130-af8a-b1586aedf8ee",
                "ProposalId": "52da18fb-64ec-4d00-9484-fdb0b67ef678",
                "Choices": [
                    {
                        "QuestionId": "36f06c15-5a2d-4c7c-bf56-ffb2affb8320",
                        "ChoiceId": "c17d31d5-3bea-41b9-91fc-e9adba00daee",
                    }
                ],
            },
            {
                "ObjectType": "VoteBallot",
                "ObjectVersion": "1.0.0",
                "VoteId": "c9491488-9176-4130-af8a-b1586aedf8ee",
                "ProposalId": "52da18fb-64ec-4d00-9484-fdb0b67ef678",
                "Choices": [
                    {
                        "QuestionId": "36f06c15-5a2d-4c7c-bf56-ffb2affb8320",
                        "ChoiceId": "c17d31d5-3bea-41b9-91fc-e9adba00daee",
                    }
                ],
            },
        ]

        self.counter = 0

    def next(self):

        obj = {
            "tx_hash": f"hash{self.counter}",
            "metadata": self.returnvals[self.counter],
        }
        self.counter = self.counter + 1
        if self.counter == 3:
            self.counter = 0
        return obj

    def ack(self, arg):
        pass
