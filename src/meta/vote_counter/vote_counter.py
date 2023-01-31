from __future__ import annotations

from lib import schema_validator, metadata_utils


class VoteCounter:
    def vote_version(self):
        return "1.0.0"

    def process_vote(self, ballot_metadata: dict, proposal_metadata: dict):
        """Validates a vote and returns it's results

        Parameters:
        ballot_metadata: ballot_metadata of the vote
        proposal_metadata: the proposal this vote relates to (ballot_metadata object)

        Returns:
        object:
            status: bool
            errors: optional array of strings
            results: the vote result in json format

        """

        errors = []

        # Make sure received metadata follos spec
        valid_ballot = schema_validator.validate_vote(
            ballot_metadata, schemapath="src/model/json_schemas/"
        )

        valid_proposal = schema_validator.validate_proposal(
            proposal_metadata, schemapath="src/model/json_schemas/"
        )

        if valid_ballot is False:
            errors.append("Schema failed for voter ballot metadata!")
        if valid_proposal is False:
            errors.append("Schema failed for proposal metadata!")

        # Make sure vote is from our current version
        if ballot_metadata["ObjectVersion"] != self.vote_version():
            errors.append(
                f"Invalid version! Expected {self.vote_version()}, but got {ballot_metadata['ObjectVersion']}"
            )

        # Make sure vote proposal ID is equal to the one from the proposal we received
        if ballot_metadata["ProposalId"] != proposal_metadata["ProposalId"]:
            errors.append(
                f"Got two different proposal IDs {ballot_metadata['ProposalId']} and {proposal_metadata['ProposalId']}"
            )

        if len(errors) > 0:
            return {"status": False, "errors": errors}

        # Make sure every vote choice has a corresponding question
        # and choice in the proposal then return the choices

        results = {}

        for choice in ballot_metadata["Choices"]:
            question_identifier = choice["QuestionId"]

            question = next(
                (
                    x
                    for x in proposal_metadata["Questions"]
                    if x["QuestionId"] == question_identifier
                )
            )

            if not question_identifier in results:
                results[question_identifier] = {
                    "question_id": question_identifier,
                    "question_name": metadata_utils.parse_string_list(
                        question["Question"]
                    ),
                    "responses": [],
                }

            choice_identifier = choice["ChoiceId"]
            choice = next(
                (x for x in question["Choices"] if x["ChoiceId"] == choice_identifier)
            )

            if choice is None:
                errors.append(
                    f"Choice {choice['ChoiceId']} not found in proposal metadata!"
                )
            else:
                results[question_identifier]["responses"].append(
                    {"choice_id": choice_identifier, "choice_name": choice["Name"]}
                )

            if len(results[question_identifier]["responses"]) > question["ChoiceLimit"]:
                error = f"Question {question['Question']} surpassed choice limit of {question['ChoiceLimit']}"

                if error not in errors:
                    errors.append(error)

        if len(errors) > 0:
            return {"status": False, "errors": errors}

        return {"status": True, "results": list(results.values())}
