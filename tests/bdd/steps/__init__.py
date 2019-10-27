from startup_settings import SETTINGS
import datetime

from tests.utils import NewDate

if not isinstance(datetime.date, NewDate):  # freeze time =)
    datetime.date = NewDate

SETTINGS['config_path'] = 'config_for_tests.py'

