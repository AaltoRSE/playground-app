from flask import Flask
from flask_bootstrap import Bootstrap
import logging
import os

logger = logging.getLogger('playground_app')
app = Flask('playground_app')
os.environ['LOGIN_CONFIG'] = 'eu-login'

from views import *

app.secret_key = os.environ['SECRET_KEY']
bootstrap = Bootstrap(app)
logger.info("Starting UI")

