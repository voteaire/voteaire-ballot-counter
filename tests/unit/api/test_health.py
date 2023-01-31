import sys

from unit.api.fixtures import api


def test_healthcheck(api, monkeypatch):
    client, app = api

    sys.path.append("src")

    monkeypatch.setattr("api.health.VERSION", 1)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "version": 1}

    class FakeSession:
        def __init__(self):
            pass

        def execute(self):
            raise Exception()

    class FakeDB:
        def __init__(self):
            self.session = FakeSession()

    monkeypatch.setattr("api.health.db", FakeDB())

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "fail", "version": 1}
