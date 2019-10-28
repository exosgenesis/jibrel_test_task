import time
from datetime import date, timedelta
from functools import reduce

from flask import request
from sqlalchemy.exc import IntegrityError

from models import Currency, Rate
from app import app, db, auth
from flask_restful import Resource, Api, abort


api = Api(app)

GRABBER_WORKER = 'GRABBER_WORKER'


class CurrenciesRes(Resource):
    @auth.login_required
    def get(self):
        return list(map(lambda x: x.to_dict(), Currency.query.paginate().items))

    @auth.login_required
    def post(self):
        json_data = request.get_json()
        curr = Currency.new_from_dict(json_data)
        db.session.add(curr)

        try:
            db.session.commit()
        except IntegrityError as e:
            if e.orig.args[0] == 1062:
                abort(400, message='Currency already exist')

        if GRABBER_WORKER in app.config:
            app.config[GRABBER_WORKER].notify()

        return curr.to_dict(), 201


class CurrencyRes(Resource):
    @auth.login_required
    def get(self, cid):
        return Currency.query.filter(Currency.id == cid).first_or_404().to_dict()

    @auth.login_required
    def delete(self, cid):
        curr = Currency.query.filter(Currency.id == cid).first_or_404()
        db.session.delete(curr)
        Rate.query.filter(Rate.currency_id == cid).delete()
        db.session.commit()
        return '', 204


class RateRes(Resource):
    @auth.login_required
    def get(self, cid):
        depth = app.config['DEPTH']
        end = date.today()
        start = end - timedelta(depth)
        rates = Rate.query.filter(Rate.currency_id == cid, Rate.date.between(start, end)).all()

        if not rates:
            abort(404)

        res = {
            'rate': max(rates, key=lambda o: o.date).rate,
            'average_by_day': reduce(lambda acc, x: acc + x.volume, rates, 0.0) / len(rates),
            'depth': depth
        }
        return res


class RatesGrabberRes(Resource):
    # only for bebug
    def post(self):
        if GRABBER_WORKER not in app.config:
            abort(404, message='grabber instance not bound')

        if app.config['NO_BACKGROUND']:
            app.config[GRABBER_WORKER].grab_in_this_thread()
            return {'message': 'grabbed rates'}, 200
        else:
            app.config[GRABBER_WORKER].notify()
            return {'message': 'sent signal to grabber'}, 200


api.add_resource(CurrenciesRes, '/currencies')
api.add_resource(CurrencyRes, '/currency/<cid>')
api.add_resource(RateRes, '/rate/<cid>')

if app.config['DEBUG']:
    api.add_resource(RatesGrabberRes, '/ratesgrabber')
