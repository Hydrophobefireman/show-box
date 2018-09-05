import psycopg2
from flask_sqlalchemy import SQLAlchemy
import sys


def add_to_db(data: tuple) -> str:
    from get import db, tvData

    assert isinstance(data, tuple) and len(data) == 4
    col = tvData(*data)
    db.session.add(col)
    db.session.commit()
    return col


def req_db(data: tuple) -> str:
    from get import db, tvRequests

    assert isinstance(data, tuple) and len(data) == 2
    col = tvRequests(*data)
    db.session.add(col)
    db.session.commit()
    return col
