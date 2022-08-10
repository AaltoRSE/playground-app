from flask import Flask, session
from flask_bootstrap import Bootstrap
import logging
import os

logger = logging.getLogger(__name__)
app = Flask(__name__)
os.environ['LOGIN_CONFIG'] = 'dev-login'
from views import *

if __name__ == "__main__":
    app.secret_key = 'dev'
    bootstrap = Bootstrap(app)
    logger.info("Starting UI")
    app.run()
