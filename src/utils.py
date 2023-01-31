from __future__ import annotations

import requests
import json

from meta.chain_providers import blockfrost

API = "http://localhost:8080/"

# print(blockfrost.get_epoch_snapshot("stake_test1uz6pf4cruzggqytel5f7z8sa0ne7lctp005hazjpv6f9mwcz5uj6c", 190))


def simple_serialize_object(obj: dict):
    serialized = ""
    for key, value in obj.items():
        if isinstance(value, dict):
            serialized += f",{key}={simple_serialize_object(value)}"
        elif isinstance(value, list):
            serialized += f",{key}={simple_serialize_array(value)}"
        else:
            serialized += f",{key}={str(value)}"

    return serialized.lstrip(",")


def simple_serialize_array(lst: list):
    serialized = ""
    for value in lst:
        if isinstance(value, dict):
            serialized += f",{simple_serialize_object(value)}"
        elif isinstance(value, list):
            serialized += f",{simple_serialize_array(value)}"
        else:
            serialized += f",{str(value)}"

    return serialized.lstrip(",")


def json_to_cli(string):
    # return string
    return string.replace('"', '\\"').replace("{", "\\{").replace("}", "\\}")


def test_api(endpoint, method="GET", params={}, headers={}, body={}):
    if method == "GET":
        r = requests.get(API + endpoint.strip("/"), params=params, headers=headers)
    elif method == "POST":
        if body:
            headers["Content-Type"] = "application/json"

        r = requests.post(API + endpoint.strip("/"), json=body, headers=headers)
    else:
        raise Exception("Method must be either GET or POST")

    print(r.status_code)
    print(r.json())


# test_api("/chain/info", method="GET")

# test_api("/proposal/52da18fb-64ec-4d00-9484-fdb0b67ef678/results")

# test_api("/vote/create", method="POST", body={
#     "Content-Type": "application/json",
#     "proposal_id": "52da18fb-64ec-4d00-9484-fdb0b67ef678",
#     "version": "1.0.0",
#     "voter_stake_address": "stake18du387djiw234ih23k4jh",
#     "question_responses": [{
#         "question_id": "36f06c15-5a2d-4c7c-bf56-ffb2affb8320",
#         "responses": ["c17d31d5-3bea-41b9-91fc-e9adba00daee"]
#     }]
# })


# test_api("/proposal/list", method="GET", params={"count": 10, "page": 1, "order": "asc"})
# test_api("/proposal/52da18fb-64ec-4d00-9484-fdb0b67ef678", method="GET")

# test_api("proposal/create", method="POST", body={
#     "address": "addr_test123",
#     "version": "1.0.0",
#     "network_id": "Voteaire - Trivia",
#     "title": "Friends Trivia",
#     "ballot_type": {
#         "name": "Simple",
#         "snapshot_epoch": 247
#     },
#     "creator_stake_address": "stake123",
#     "questions": [
#         {
#             "question": "What was Chandler's job?",
#             "choice_limit": 1,
#             "choices": [
#                 {
#                     "choice": "Accountant"
#                 },
#                 {
#                     "choice": "Statistical Analysis"
#                 },
#                 {
#                     "choice": "Graphic Designer"
#                 }
#             ]
#         },
#         {
#             "question": "What was the name of Phoeby's twin sister?",
#             "choice_limit": 2,
#             "choices": [
#                 {
#                     "choice": "Alice"
#                 },
#                 {
#                     "choice": "Erika"
#                 },
#                 {
#                     "choice": "Ursula"
#                 }
#             ]
#         }
#     ],
#     "start_epoch": 450,
#     "end_epoch": 451
# })
