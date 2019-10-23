from startup_settings import SETTINGS

SETTINGS['config_path'] = 'config_for_tests.py'

from api import app

def test_hello():
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    assert True
