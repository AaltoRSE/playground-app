from flask import Flask, session
from flask_bootstrap import Bootstrap
import logging
import os

logger = logging.getLogger(__name__)
app = Flask(__name__)
https_key="/etc/letsencrypt/live/playground.ki-lab.nrw/privkey.pem"
https_chain="/etc/letsencrypt/live/playground.ki-lab.nrw/fullchain.pem"
os.environ['LOGIN_CONFIG'] = 'eu-login'

from views import *

if __name__ == "__main__":
    app.secret_key = 'dev'
    bootstrap = Bootstrap(app)
    logger.info("Starting UI")
    context=(https_chain, https_key)
    app.run(host='0.0.0.0', port=443, ssl_context=context)

