import psycopg2
from flask_sqlalchemy import SQLAlchemy
import sys


def add_to_db(data):
    from get import db, tvData
    assert isinstance(data, tuple) and len(data) == 7
    url = data[1]
    if tvData.query.filter_by(url=url).first() is not None:
        raise Exception("Added Already")
    col = tvData(*data)
    db.session.add(col)
    db.session.commit()
    return col


def req_db(data):
    from get import db, tvRequests
    assert isinstance(data, tuple) and len(data) == 2
    col = tvRequests(*data)
    db.session.add(col)
    db.session.commit()
    return col
