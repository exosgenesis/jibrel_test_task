import datetime

from sqlalchemy import func

from models import db, Currency, Rate


if __name__ == '__main__':
    # todo: cascade delete testing
    db.drop_all()
    db.create_all()
    # db.session.add(Rate(currency_id=1, date=datetime.datetime.now(), rate=0.5, volume=100))
    db.session.add(Currency(name='BTC'))
    # db.session.add(Currency(name='UZS'))
    db.session.commit()
    # print(str(db.session.query(func.max(Rate.date)).filter_by(currency_id=1).scalar()))
