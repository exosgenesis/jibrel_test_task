DEBUG = False
DISABLE_AUTH = False
TARGET_CURRENCY = 'USD'
NO_BACKGROUND = False
DEPTH = 10
API_TRADE_URL = 'https://api-pub.bitfinex.com/v2/candles/trade'
RATES_UPDATES_DELAY = 60

# SQLALCHEMY_DATABASE_URI = 'sqlite:///D:\\eskess_workspace\\jibrel_test_task\\jibrel.db'
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/trades'
