from model import db

VERSION = 1


def get():
    try:
        db.session.execute("select 1")
        # TODO add more checks below
    except Exception:
        return {"status": "fail", "version": VERSION}
    return {"status": "ok", "version": VERSION}
