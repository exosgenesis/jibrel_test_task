from sqlathanor import FlaskBaseModel, initialize_flask_sqlathanor
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth

from startup_settings import SETTINGS

app = Flask(__name__)
app.config.from_pyfile(SETTINGS['config_path'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app, model_class=FlaskBaseModel)
db = initialize_flask_sqlathanor(db)

auth = HTTPBasicAuth()

USERNAME = 'admin'
PASSWORD = 'iddqd'


if app.config['DEBUG'] and app.config['DISABLE_AUTH']:
    auth.verify_password(lambda u, p: True)
else:
    auth.verify_password(lambda u, p: USERNAME == u and PASSWORD == p)
