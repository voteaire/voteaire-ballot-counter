import pytest
import connexion
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="class")
def session():

    # engine = create_engine("sqlite://", echo=True)
    # Session = sessionmaker()
    # Session.configure(bind=engine)
    # with Session() as session:
    #     yield session
    sys.path.append("src")

    from model import db

    options = {"swagger_ui": False}
    app = connexion.FlaskApp(
        __name__, specification_dir="../../../src/openapi/", options=options
    )

    # # validate responses means that if our methods return something not legit, the test will fail
    # app.add_api('openapi-spec.yml', validate_responses=True)

    app = app.app

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield db.session
