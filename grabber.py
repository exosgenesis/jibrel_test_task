import time
from datetime import date, timedelta
from collections import OrderedDict

import requests
from sqlalchemy import func

from models import Currency, Rate, db


class RatesGrabber:

    def __init__(self, config):
        self._last_date_grab = None
        self._last_currencies = set()

        self._api_trade_url = config['API_TRADE_URL']
        self._target_curr = config['TARGET_CURRENCY']
        self._depth = config['DEPTH']

    def grab(self):
        currs = Currency.query.all()
        curr_ids = {c.id for c in currs}

        today = date.today()
        end_date = today + timedelta(days=1)
        default_start_date = today - timedelta(days=self._depth)

        if curr_ids == self._last_currencies and self._last_date_grab == end_date:
            # same currencies, same day -> just update last rates
            for curr in currs:
                self._update_rate(curr, end_date)
        else:
            # first launch, new currencies or new day -> read and add new day rates
            for curr in currs:
                self._init_rates(curr, default_start_date, end_date)

        db.session.commit()
        self._last_date_grab = end_date
        self._last_currencies = curr_ids

    def _update_rate(self, curr, end_date):
        exist_rate = self._get_last_rate(curr.id)
        rates = self._fetch_rates(curr, exist_rate.date, end_date)
        new_rate = rates[0]
        exist_rate.rate = new_rate.rate
        exist_rate.volume = new_rate.volume

    def _init_rates(self, curr, default_start_date, end_date):
        rate = self._get_last_rate(curr.id)

        if rate is None or end_date - rate.date > timedelta(days=self._depth):
            # if db is empty or records are too old
            rates = self._fetch_rates(curr, default_start_date, end_date)
        else:
            rates = self._fetch_rates(curr, rate.date, end_date)
            db.session.delete(rate)

        db.session.add_all(rates)

    def _get_last_rate(self, curr_id):
        id = db.session.query(func.max(Rate.id)).filter_by(currency_id=curr_id).scalar()
        if not id:
            return None
        return Rate.query.filter_by(id=id).first()

    def _fetch_rates(self, currency, start_date, end_date):
        req_url = '{trade_url}:1h:t{curr}{target_curr}/hist'.format(
            trade_url=self._api_trade_url,
            curr=currency.name,
            target_curr=self._target_curr
        )
        params = {
            'limit': 24 * self._depth,
            'sort': 1,
            'start': self.timestamp(start_date),
            'end': self.timestamp(end_date)
        }

        res = requests.get(req_url, params).json()
        return self._rates_grouped_by_days(currency, res)

    @staticmethod
    def timestamp(_date):
        return int(time.mktime(_date.timetuple()) * 1000)

    def _rates_grouped_by_days(self, curr, resp):
        # response row structure: [ MTS, OPEN, CLOSE, HIGH, LOW, VOLUME ]
        # tmp row structure: [date, rate, volume]
        print('-----------RESPONSE: ' + str(resp))
        tmp = [(date.fromtimestamp(x[0] / 1000), x[2], x[5]) for x in resp]

        groups = OrderedDict()  # {date -> [closed rate, total volume]}

        for row in tmp:
            k = row[0]
            rate = row[1]
            row_volume = row[2]
            all_volume = groups.get(k, [0, 0])[1]
            groups[k] = [rate, all_volume + row_volume]

        return [Rate(currency_id=curr.id, date=k, rate=v[0], volume=v[1])
                for k, v in groups.items()]
