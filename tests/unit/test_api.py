from datetime import date, timedelta

import pytest as pytest
from flask import json

from api import app, db
from models import Currency, Rate


@pytest.fixture(autouse=True)
def prepare_db():
    db.drop_all()
    db.create_all()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()


def test_list(client):
    db.session.add(Currency(name='USD'))
    db.session.add(Currency(name='UZS'))
    db.session.add(Currency(name='RUB'))
    db.session.add(Currency(name='ETH'))
    db.session.add(Currency(name='BTC'))
    db.session.commit()

    rs = client.get('/currencies')
    # assert EXPECTED == ACTUAL
    assert rs.status_code == 200

    names = list(map(lambda j: j['name'], rs.json))

    assert 'USD' in names
    assert 'UZS' in names
    assert 'RUB' in names
    assert 'ETH' in names
    assert 'BTC' in names


def test_pagination_1(client):
    db.session.add(Currency(name='USD'))
    db.session.add(Currency(name='UZS'))
    db.session.add(Currency(name='RUB'))
    db.session.add(Currency(name='ETH'))
    db.session.add(Currency(name='BTC'))
    db.session.commit()

    rs = client.get('/currencies?per_page=3')
    assert rs.status_code == 200

    assert len(rs.json) == 3


def test_pagination_2(client):
    db.session.add(Currency(name='USD'))
    db.session.add(Currency(name='UZS'))
    db.session.add(Currency(name='RUB'))
    db.session.add(Currency(name='ETH'))
    db.session.add(Currency(name='BTC'))
    db.session.commit()

    rs = client.get('/currencies?per_page=3&page=1')
    assert rs.status_code == 200
    names_p1 = list(map(lambda j: j['name'], rs.json))

    rs = client.get('/currencies?per_page=3&page=2')
    assert rs.status_code == 200
    names_p2 = list(map(lambda j: j['name'], rs.json))

    names = names_p1 + names_p2

    assert len(names_p1) == 3
    assert len(names_p2) == 2
    assert 'USD' in names
    assert 'UZS' in names
    assert 'RUB' in names
    assert 'ETH' in names
    assert 'BTC' in names


def test_get(client):
    db.session.add(Currency(name='BTC'))
    db.session.add(Currency(name='ETH'))
    db.session.commit()

    rs = client.get('/currency/1')
    assert rs.status_code == 200

    btc = rs.json

    rs = client.get('/currency/2')
    assert rs.status_code == 200

    eth = rs.json

    assert btc['id'] == 1
    assert btc['name'] == 'BTC'
    assert eth['id'] == 2
    assert eth['name'] == 'ETH'


def test_delete_positive(client):
    btc = Currency(name='BTC')
    btc.rates.append(Rate(date=date.today(), rate=1, volume=1))

    eth = Currency(name='ETH')
    eth.rates.append(Rate(date=date.today(), rate=1, volume=1))

    db.session.add(btc)
    db.session.add(eth)
    db.session.commit()

    rs = client.delete('/currency/1')
    assert rs.status_code == 204

    btc = Currency.query.filter(Currency.name == 'BTC').first()
    assert btc is None

    eth = Currency.query.filter(Currency.name == 'ETH').first()
    assert eth is not None

    assert 0 == Rate.query.filter_by(currency_id=1).count()
    assert 0 != len(eth.rates)


def test_delete_negative(client):
    db.session.add(Currency(name='ETH'))
    db.session.commit()

    rs = client.delete('/currency/2')
    assert rs.status_code == 404

    eth = Currency.query.filter(Currency.name == 'ETH').first()
    assert eth is not None


def test_curr_add_positive(client):
    db.session.add(Currency(name='ETH'))
    db.session.commit()

    j_btc = json.dumps({'name': 'BTC'})

    rs = client.post('/currencies', data=j_btc, content_type='application/json')
    assert 201 == rs.status_code

    r_btc = rs.json

    assert 'BTC' == r_btc['name']
    assert isinstance(r_btc['id'], int)

    btc = Currency.query.filter(Currency.id == r_btc['id']).first()
    assert btc is not None

    assert r_btc['id'] == btc.id
    assert 'BTC' == btc.name


def test_curr_add_negative(client):
    db.session.add(Currency(name='ETH'))
    db.session.commit()

    j_eth = json.dumps({'name': 'ETH'})

    rs = client.post('/currencies', data=j_eth, content_type='application/json')
    assert 200 != rs.status_code

    assert 1 == Currency.query.count()


def test_rate(client):
    xpr = Currency(name='XPR')
    btc = Currency(name='BTC')

    db.session.add(xpr)
    db.session.add(btc)
    db.session.add(Currency(name='ETH'))

    xpr.rates.append(Rate(date=date.today() - timedelta(days=1), rate=1500, volume=5000))
    btc.rates.append(Rate(date=date.today(), rate=4000, volume=20000))
    xpr.rates.append(Rate(date=date.today(), rate=1600, volume=7000))

    db.session.commit()

    rs = client.get('/rate/1')
    xpr_rate = rs.json
    assert 200 == rs.status_code

    rs = client.get('/rate/2')
    btc_rate = rs.json
    assert 200 == rs.status_code

    rs = client.get('/rate/3')
    assert 404 == rs.status_code

    assert 1600 == xpr_rate['rate']
    assert 6000 == xpr_rate['average_by_day']
    assert 4000 == btc_rate['rate']
    assert 20000 == btc_rate['average_by_day']
