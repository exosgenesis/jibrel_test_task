import time

from sqlalchemy.exc import OperationalError

from models import db


def init_db():
    while True:
        try:
            db.create_all()
            return
        except OperationalError as e:
            print(e)
            if e.orig.args[0] == 2003:  # Can't connect, perhaps db not ready yet
                time.sleep(3)
            else:
                raise e


if __name__ == '__main__':
    init_db()
