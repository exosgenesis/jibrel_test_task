import datetime
from config_for_tests import API_TRADE_URL, TARGET_CURRENCY


class NewDate(datetime.date):
    # fixed data useful for tests
    @classmethod
    def today(cls):
        return cls(2010, 6, 21)






def get_trade_url(curr_name):
    return '{trade_url}:1h:t{curr}{target_curr}/hist'.format(
        trade_url=API_TRADE_URL,
        curr=curr_name,
        target_curr=TARGET_CURRENCY
    )
