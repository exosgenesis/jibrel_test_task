from datetime import date, timedelta
from functools import reduce

from flask import request

from grabber_worker import GrabberWorker
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
        json_data = request.get_json(force=True)
        curr = Currency.new_from_dict(json_data)
        db.session.add(curr)

        try:
            db.session.commit()
        except Exception as e:
            # todo: unique error
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
        db.session.commit()
        return '', 204


class RateRes(Resource):
    @auth.login_required
    def get(self, cid):
        end = date.today()
        start = end - timedelta(days=10)
        rates = Rate.query.filter(Rate.currency_id == cid, Rate.date.between(start, end)).all()

        if not rates:
            abort(404)

        res = {
            'rate': max(rates, key=lambda o: o.date).rate,
            'average_by_day': reduce(lambda acc, x: acc + x.volume, rates, 0.0) / len(rates),
            'depth': 10
        }
        return res


class RatesGrabberRes(Resource):
    # only for bebug
    def post(self):
        if GRABBER_WORKER in app.config:
            app.config[GRABBER_WORKER].grab_in_this_thread()
            return {'message': 'rates has been grabbed'}, 200

        abort(404, message='grabber instance not bound')


api.add_resource(CurrenciesRes, '/currencies')
api.add_resource(CurrencyRes, '/currency/<cid>')
api.add_resource(RateRes, '/rate/<cid>')

if app.config['DEBUG']:
    api.add_resource(RatesGrabberRes, '/ratesgrabber')


if __name__ == '__main__':
    grabber_worker = GrabberWorker(app.config)
    app.config[GRABBER_WORKER] = grabber_worker
    grabber_worker.start()

    app.run(port=5001)
    grabber_worker.stop()