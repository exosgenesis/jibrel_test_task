import time
from datetime import timedelta, date

import pytest
import responses

from app import app, db
from grabber import RatesGrabber
from models import Currency, Rate

from config_for_tests import DEPTH
from tests.utils import get_trade_url


@pytest.fixture(autouse=True)
def prepare_db():
    db.drop_all()
    db.create_all()
    

@pytest.fixture
def today():
    return date.today()


@pytest.fixture
def grabber():
    return RatesGrabber(app.config)


@pytest.fixture(scope="module")
def unix_ts():
    def f(_date, daydelta=0, hourdelta=0):
        d = _date + timedelta(days=daydelta, hours=hourdelta)
        return int(time.mktime(d.timetuple()) * 1000)
    return f


@pytest.fixture(scope="module")
def mkrow():
    def f(ts, rate, volume):
        # response row structure: [ MTS, OPEN, CLOSE, HIGH, LOW, VOLUME ]
        return [ts, 1, rate, 1, 1, volume]
    return f


@pytest.fixture(scope="module")
def extract_params():
    def f(rq):
        if '?' not in rq.url:
            return {}
        param_pairs = rq.url.split('?')[1].split('&')
        return dict(map(lambda p: p.split('='), param_pairs))
    return f


@responses.activate
def test_empty_db(grabber, today, extract_params, unix_ts):
    db.session.add(Currency(name='BTC'))
    db.session.commit()

    responses.add(responses.GET, get_trade_url('BTC'), status=200, json=[])

    grabber.grab()

    rq = responses.calls[0].request

    rq_url = rq.url.split('?')[0]
    params = extract_params(rq)

    # assert EXPECTED == ACTUAL
    assert get_trade_url('BTC') == rq_url
    assert params['start']
    assert params['end']
    assert unix_ts(today, daydelta=-DEPTH) == int(params['start'])
    assert unix_ts(today, daydelta=1) == int(params['end'])


@responses.activate
def test_not_empty_db(grabber, today, extract_params, unix_ts):
    curr = Currency(name='BTC')
    curr.rates.append(Rate(date=today - timedelta(days=5), rate=1, volume=1))
    curr.rates.append(Rate(date=today - timedelta(days=4), rate=1, volume=1))

    db.session.add(curr)
    db.session.commit()

    responses.add(responses.GET, get_trade_url('BTC'), status=200, json=[])

    grabber.grab()

    rq = responses.calls[0].request

    rq_url = rq.url.split('?')[0]
    params = extract_params(rq)

    assert get_trade_url('BTC') == rq_url
    assert params['start']
    assert params['end']
    assert unix_ts(today, daydelta=-4) == int(params['start'])
    assert unix_ts(today, daydelta=1) == int(params['end'])


@responses.activate
def test_update_db(grabber, today, mkrow, extract_params, unix_ts):
    curr = Currency(name='BTC')
    curr.rates.append(Rate(date=today, rate=1, volume=1))
    curr.rates.append(Rate(date=today - timedelta(days=1), rate=1, volume=1))
    curr.rates.append(Rate(date=today - timedelta(days=2), rate=1, volume=1))

    db.session.add(curr)
    db.session.commit()

    responses.add(responses.GET, get_trade_url('BTC'), status=200,
                  json=[mkrow(unix_ts(today, hourdelta=12), 1, 1)])

    grabber.grab()  # first launch
    grabber.grab()  # update last rates

    assert len(responses.calls) == 2

    rq = responses.calls[1].request

    rq_url = rq.url.split('?')[0]
    params = extract_params(rq)

    assert get_trade_url('BTC') == rq_url
    assert params['start']
    assert params['end']
    assert unix_ts(today) == int(params['start'])
    assert unix_ts(today, daydelta=1) == int(params['end'])


@responses.activate
def test_grouping_in_db(grabber, today, mkrow, unix_ts):
    btc = Currency(name='BTC')
    btc.rates.append(Rate(date=today - timedelta(days=2), rate=1, volume=1))
    btc.rates.append(Rate(date=today - timedelta(days=3), rate=1, volume=1))

    xpr = Currency(name='XPR')
    xpr.rates.append(Rate(date=today, rate=1, volume=1))
    xpr.rates.append(Rate(date=today - timedelta(days=1), rate=1, volume=1))

    eth = Currency(name='ETH')

    db.session.add(btc)
    db.session.add(xpr)
    db.session.add(eth)
    db.session.commit()

    responses.add(responses.GET, get_trade_url('BTC'), status=200, json=[
        mkrow(unix_ts(today, daydelta=-2), 4998, 1),
        mkrow(unix_ts(today, daydelta=-1), 4999, 10000),
        mkrow(unix_ts(today), 4998, 4000),
        mkrow(unix_ts(today, hourdelta=6), 4999, 2000),
        mkrow(unix_ts(today, hourdelta=12), 5000, 1000)
    ])

    responses.add(responses.GET, get_trade_url('XPR'), status=200, json=[
        mkrow(unix_ts(today), 502, 500),
        mkrow(unix_ts(today, hourdelta=2), 503, 600),
        mkrow(unix_ts(today, hourdelta=4), 504, 700)
    ])

    responses.add(responses.GET, get_trade_url('ETH'), status=200, json=[
        mkrow(unix_ts(today, daydelta=-1, hourdelta=2), 47, 1000),
        mkrow(unix_ts(today, daydelta=-1, hourdelta=4), 48, 400),
        mkrow(unix_ts(today, hourdelta=2), 49, 200),
        mkrow(unix_ts(today, hourdelta=4), 50, 100)
    ])

    grabber.grab()

    assert 3 == len(responses.calls)

    assert 4 == len(btc.rates)

    assert 5000 == btc.rates[-1].rate
    assert 7000 == btc.rates[-1].volume
    assert 4999 == btc.rates[-2].rate
    assert 10000 == btc.rates[-2].volume
    assert 4998 == btc.rates[-3].rate
    assert 1 == btc.rates[-3].volume

    assert 2 == len(xpr.rates)
    assert 504 == xpr.rates[-1].rate
    assert 1800 == xpr.rates[-1].volume
    assert 1 == xpr.rates[-2].rate
    assert 1 == xpr.rates[-2].volume

    assert 2 == len(eth.rates)
    assert 50 == eth.rates[-1].rate
    assert 300 == eth.rates[-1].volume
    assert 48 == eth.rates[-2].rate
    assert 1400 == eth.rates[-2].volume
