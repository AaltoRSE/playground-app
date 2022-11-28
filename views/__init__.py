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
from functools import wraps
from flask import render_template, redirect, send_file, abort
from objectModelPlayground.PipelineManager import PipelineManager
from binascii import hexlify

import os
import base64
import json
import threading
import logging


def logged_in(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'username' in session:
            if 'refresh' not in session:
                session['refresh'] = []
            return f(*args, **kwargs)
        else:
            return render_login()
    return decorated_func


logger = logging.getLogger(__name__)

logger.info('LOGIN_CONFIG = '+os.environ['LOGIN_CONFIG'])
if os.environ['LOGIN_CONFIG'] == 'eu-login':
    from eu_login import *
else:
    from dev_login import *
from app import app

pipelineThreads = {}
pathSolutionZips = "solutionZips/"
pathSolutions = "solutions/"
pm = PipelineManager(pathSolutions)


def get_base_dir(user, deployment):
    return os.path.join(os.getcwd(), "solutions", user, deployment)

@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    # session.pop('current_deployment_id')
    print(f'handle_error(): {e}')
    try:
        x,pipeline_id = e.args
        if(pipeline_id in pm.get_pipeline_ids(session['username'])):
            _remove_pipeline(pipeline_id=pipeline_id)
    except:
        pass

    return redirect('/')


@app.route('/', methods=["GET"])
def home():
    logger.info("enter home()")
    if request.method == "GET":
        if "username" not in session:
            return render_login()
        else:
            pipelines = pm.get_pipeline_ids(session['username'])
            if len(pipelines) > 0:
                return redirect('/dashboard')

    return render_template('index.html')


@app.route('/dashboard', methods=['GET'])
@logged_in
def dashboard():
    logger.info("show deployments..")
    user = session['username']
    deployment_list = pm.get_pipelines_user(user)
    if len(deployment_list) < 1:
        return redirect('/')

    # set the current deployment
    current_deployment_id = session['current_deployment_id'] if 'current_deployment_id' in session else deployment_list[0].get_pipeline_id()
    selection = request.args.get('selected_deployment_id', 'None', type=str)
    if selection != 'None' and selection in pm.get_pipeline_ids(user):
        current_deployment_id = selection
    session['current_deployment_id'] = current_deployment_id
    logger.info(f"Display nodes in a deployment. current_user: {user} - deployment_id: {current_deployment_id}")

    # setup page variables
    pipeline = pm.get_pipeline(user_name=user, pipeline_id=current_deployment_id)
    user_folder = os.path.join(user, current_deployment_id)
    if pipeline.get_status() == "Not Ready" and len(session['refresh'])<1:
        session['refresh']=[24,12,6,3,3]
    if pipeline.get_status() == 'Ready':
        session['refresh']=[]
    logger.info("rendering dashboard.html..")
    return render_template("dashboard.html", pipeline=pipeline, user_folder=user_folder, deployment_list=deployment_list)


@app.route('/reset', methods=['GET'])
@logged_in
def reset():
    logger.info("Reset Deployment..")
    if 'current_deployment_id' in session:
        pipeline = pm.get_pipeline(user_name=session['username'], pipeline_id=session['current_deployment_id'])
        pipeline.pull_and_rollout()
        session['refresh'] = [3,3]
        logger.info("Reset Deployment successful.")

    return redirect('/dashboard')


def _remove_pipeline(pipeline_id):
    pipeline = pm.get_pipeline(user_name=session['username'], pipeline_id=pipeline_id)
    pipeline.remove_pipeline()

@app.route('/delete', methods=['GET'])
@logged_in
def delete():
    logger.info("Delete Deployments")
    if 'current_deployment_id' in session:
        _remove_pipeline(pipeline_id=session['current_deployment_id'])
        session.pop('current_deployment_id')

    return redirect('/')  # redirect to home page with message

@app.route('/logs/', methods=['GET'])
@app.route('/pipeline_logs/', methods=['GET'])
@logged_in
def logs():
    if 'current_deployment_id' in session:
        pipeline = pm.get_pipeline(user_name=session['username'], pipeline_id=session['current_deployment_id'])
        logs = pipeline.get_pipeline_logs().split("\n")
        return render_template('logs.html', text=logs)

    return redirect('/')  # redirect to home page with message

@app.route('/shared_folder/', methods=['GET'])
@logged_in
def dir_listing():
    req_path = request.args.get('path', default='', type=str)
    pipeline = pm.get_pipeline(user_name=session['username'], pipeline_id=session['current_deployment_id'])
    BASE_DIR = pipeline.get_shared_folder_path()
    print(f"BASE_DIR = {BASE_DIR}")

    if not req_path == '':
        req_path = req_path.lstrip("/")
    abs_path = os.path.join(BASE_DIR, req_path)

    if not os.path.exists(abs_path):
        return abort(404)

        # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

        # Show directory contents
    files = [os.path.join(req_path,file) for file in os.listdir(abs_path)]
    return render_template('files.html', files=files)


@app.route('/run', methods=['GET'])
@logged_in
def run():
    pipeline = pm.get_pipeline(user_name=session['username'], pipeline_id=session['current_deployment_id'])
    # pipeline.runOrchestratorClient()
    pipelineThreads[session['username']] = threading.Thread(target=pipeline.run_orchestrator_client, args=())
    pipelineThreads[session['username']].start()
    session['refresh'] = [3,3,3,3,3]

    return redirect('/dashboard')  # redirect to home page with message


def decode_and_write_solution_zip(data, username):
    directory_solution_zip = pathSolutionZips + username
    os.makedirs(directory_solution_zip, exist_ok=True)
    path_solution_zip = f"{directory_solution_zip}/solution.zip"
    filedata = base64.b64decode(data)
    with open(path_solution_zip, 'wb+') as f:
        f.write(filedata)
    logger.info(f"solution.zip successfully added to {directory_solution_zip}")
    return directory_solution_zip


def is_allowed_client(client):
    try:
        with open("config.json") as f:
            data = json.load(f)
        allowed_clients = data['allowed_ip_addresses']

        return client in allowed_clients
    except Exception as e:
        raise Exception("\n -> config.json for allowed_ip_addresses could not be found! ") from e

@app.route('/deploy_solution', methods=['POST'])
def deploy_solution():
    body = {}
    logger.info("enter deploy_solution")
    try:
        body = request.get_json(force=True)
        logger.info("got json")
        client = request.remote_addr
        if not is_allowed_client(client):
            response = app.response_class(
                response=f"Not allowed for your domain: {client}",
                status=401
            )
            return response

        required = ('solution', 'username')
        if not all([r in body.keys() for r in required]):
            abort(400, "Required:" + ", ".join(required))

        username = hexlify(body['username'].lower().strip().encode()).decode('utf-8')
        logger.info(f"got solution and username: {username}")
        directory_solution_zip = decode_and_write_solution_zip(body['solution'], username)
        pipeline_id = pm.create_pipeline(username, directory_solution_zip)
        response = app.response_class(response=f'/dashboard?selected_deployment_id={pipeline_id}', status=200)
        return response
    except Exception as e:
        logger.info(f"exception in deploy_solution: {str(e)}")
        response = app.response_class(
            response=f"deploy solution failed with: {str(e)}",
            status=500
        )
        return response
