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
from flask import Flask
from flask_bootstrap import Bootstrap4
import logging
import os
from config_importer import import_config
import json

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s:%(lineno)d\t- %(levelname)s - %(message)s')

config_file_path = "config.json"
config = import_config(config_file_path)
app = Flask(__name__)
os.environ['LOGIN_CONFIG'] = "dev-login" if config.get("login_config") is None else config.get("login_config")
os.environ['FEDERATION_APITOKEN'] = json.dumps(config.get("ai_builder_federation_services")) if config.get("ai_builder_federation_services") else None 
from views import *

if __name__ == "__main__":

    app.secret_key = 'dev' if os.environ.get('SECRET_KEY') is None else os.environ['SECRET_KEY']
    app.config["name_kubernetes_pull_secret"] = config.get("name_kubernetes_pull_secret")
    app.config["path_kubernetes_pull_secret"] = config.get("path_kubernetes_pull_secret")
    bootstrap = Bootstrap4(app)
    logging.info("Starting UI")
    context = None
    if config.get("https_chain") and config.get("https_key"):
        context = (config.get("https_chain"), config.get("https_key"))
    app.run(debug= True, host=config.get("host"), port=config.get("port"), ssl_context=context)
