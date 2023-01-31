from sqlalchemy.exc import OperationalError


def safe_add(session, row):
    # Prevent occasional operational errors

    attempts = 5
    last_exception = None

    session.add(row)

    for _ in range(attempts):
        try:
            session.commit()
            return
        except OperationalError as e:
            last_exception = e
        except Exception as e:
            raise e

    raise last_exception
