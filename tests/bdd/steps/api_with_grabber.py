from datetime import datetime

import responses
from behave import *
from api import db, app, Currency, Rate, GRABBER_WORKER
from grabber_worker import GrabberWorker
from tests.utils import get_trade_url, NewDate


@given("Api, remote, db and grabber")
def step_impl(ctx):
    db.drop_all()
    db.create_all()
    ctx.remote_data = {}
    ctx.client = app.test_client()

    grabber_worker = GrabberWorker(app.config)
    app.config[GRABBER_WORKER] = grabber_worker
    ctx.grabber_worker = grabber_worker


@given("Api, remote, db and grabber worker")
def step_impl(ctx):
    db.drop_all()
    db.create_all()
    ctx.remote_data = {}
    ctx.client = app.test_client()

    grabber_worker = GrabberWorker(app.config)
    app.config[GRABBER_WORKER] = grabber_worker
    ctx.grabber_worker = grabber_worker
    

@given("DB contain {curr} currency with rates rows")
def step_impl(ctx, curr):
    curr = Currency(name=curr)

    for row in ctx.table:
        _date = datetime.strptime(row['date'], '%Y.%m.%d').date()
        _date = NewDate(_date.year, _date.month, _date.day)
        curr.rates.append(Rate(date=_date, rate=float(row['rate']), volume=float(row['volume'])))

    db.session.add(curr)
    db.session.commit()


@given("Remote API with data for next {curr} request")
def step_impl(ctx, curr):
    data = []

    for row in ctx.table:
        mts = int(datetime.strptime(row['MTS'], '%Y.%m.%d %H:%M').timestamp() * 1000)
        other_values = list(map(float, row.cells[1:]))
        data.append([mts] + other_values)

    ctx.remote_data[curr] = data


@then("'/currencies' request return")
def step_impl(ctx):
    expected = [{'id': int(r['id']), 'name': r['name']} for r in ctx.table.rows]
    assert expected == ctx.client.get('/currencies').json


@when("Grabber update data by schedule")
@responses.activate
def step_impl(ctx):
    for curr in ctx.remote_data.keys():
        responses.add(responses.GET, get_trade_url(curr), status=200,
                      json=ctx.remote_data[curr])

    resp = ctx.client.post('/ratesgrabber')
    assert 200 == resp.status_code


@then("'/rate/{cid}' request return {rate} rate and {avg_vol} average volume")
def step_impl(ctx, cid, rate, avg_vol):
    resp = ctx.client.get('/rate/' + cid)
    body = resp.json

    assert 200 == resp.status_code
    assert float(rate) == float(body['rate'])
    assert float(avg_vol) == float(body['average_by_day'])


@when("Add {curr} currency by API request")
def step_impl(ctx, curr):
    resp = ctx.client.post('/currencies', json={'name': curr})
    assert 201 == resp.status_code
