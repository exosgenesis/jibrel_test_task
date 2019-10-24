from startup_settings import SETTINGS
import datetime


class NewDate(datetime.date):
    @classmethod
    def today(cls):
        return cls(2010, 6, 1)


datetime.date = NewDate  # freeze time =)
SETTINGS['config_path'] = 'config_for_tests.py'
