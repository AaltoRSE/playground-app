# ===================================================================================
# Copyright (C) 2019 Fraunhofer Gesellschaft. All rights reserved.
# ===================================================================================
# This Graphene software file is distributed by Fraunhofer Gesellschaft
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END==========================================================
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
