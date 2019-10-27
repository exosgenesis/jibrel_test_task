from startup_settings import SETTINGS
import datetime

from tests.utils import NewDate

datetime.date = NewDate  # freeze time =)
SETTINGS['config_path'] = 'config_for_tests.py'
