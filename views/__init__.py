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
from flask import render_template, redirect, send_file, abort, flash
from objectModelPlayground.PipelineManager import PipelineManager
import subprocess

import os
import base64
import json
import logging
from pathlib import Path
import requests
from config_importer import import_config


def logged_in(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if "username" in session:
            if "refresh" not in session:
                session["refresh"] = []
            if "version_info" not in session:
                session["version_info"] = get_version_info()
            return f(*args, **kwargs)
        else:
            return render_login()

    return decorated_func


logger = logging.getLogger(__name__)

logger.info("LOGIN_CONFIG = " + os.environ["LOGIN_CONFIG"])

if os.environ["LOGIN_CONFIG"] == "eu-login":
    from eu_login import *
else:
    from dev_login import *
from app import app

# load the configuration
config = import_config("config.json")

pathSolutionZips = "solutionZips/"
pathSolutions = "solutions/"
pm = PipelineManager(pathSolutions, config)

ai_builder_federation_services = json.loads(os.environ.get("FEDERATION_APITOKEN", "{}"))
if ai_builder_federation_services:
    logger.info("AI-Builder federation service available")


def get_base_dir(user, deployment):
    return os.path.join(os.getcwd(), "solutions", user, deployment)


def get_version_info():
    logger.info("enter get_version_info()")
    try:
        return str(
            subprocess.run(["git", "describe", "--tags"], capture_output=True).stdout,
            "utf-8",
        )
    except Exception as e:
        print(e)
        return "version not available"


def get_current_deployment_id():
    user = session.get("username")
    deployment_id = session.get("current_deployment_id")

    if deployment_id is not None:
        return deployment_id

    pipeline_ids = pm.get_pipeline_ids(user)

    return pipeline_ids[0] if pipeline_ids else None


def clean_current_deployment():

    user = session.get("username")

    while True:
        current_deployment_id = get_current_deployment_id()
        if current_deployment_id is None:
            break

        if pm.is_healthy(
            user, current_deployment_id
        ) and current_deployment_id in pm.get_pipeline_ids(user_name=user):
            break

        session.pop("current_deployment_id", None)
        pm.remove_pipeline(user_name=user, pipeline_id=current_deployment_id)


@app.errorhandler(Exception)
def handle_error(e):
    print(f"handle_error(): {e}")
    try:
        _, pipeline_id = e.args
        if pipeline_id in pm.get_pipeline_ids(session.get("username")):
            _remove_pipeline(pipeline_id=pipeline_id)
    except:
        pass

    return redirect("/")


@app.route("/", methods=["GET"])
@logged_in
def home():
    logger.info("enter home()")
    if request.method == "GET":
        pipelines = pm.get_pipeline_ids(session.get("username"))
        if len(pipelines) > 0:
            return redirect("/dashboard")

    return render_template("index.html")


@app.route("/dashboard", methods=["GET"])
@logged_in
def dashboard():
    logger.info("show deployments..")
    user = session.get("username")
    deployment_list = pm.get_pipelines_user(user)
    if len(deployment_list) < 1:
        return redirect("/")

    clean_current_deployment()
    current_deployment_id = get_current_deployment_id()
    selection = request.args.get("selected_deployment_id", "None", type=str)
    if selection != "None" and selection in pm.get_pipeline_ids(user):
        current_deployment_id = selection
    session["current_deployment_id"] = current_deployment_id
    logger.info(
        f"Display nodes in a deployment. current_user: {user} - deployment_id: {current_deployment_id}"
    )

    # setup page variables
    pipeline = pm.get_pipeline(user_name=user, pipeline_id=current_deployment_id)
    user_folder = os.path.join(user, current_deployment_id)
    status = pipeline.get_status()
    if status == "Not Ready" and len(session["refresh"]) < 1:
        session["refresh"] = [24, 12, 6, 3, 3]
    if status == "Ready":
        session["refresh"] = []

    content_url = os.path.join(
        pathSolutions,
        session.get("username"),
        get_current_deployment_id(),
        "solution_description.html",
    )
    image_url = os.path.join(
        pathSolutions,
        session.get("username"),
        get_current_deployment_id(),
        "solution_icon.png",
    )
    heading = (
        "exist"
        if os.path.exists(content_url) or os.path.exists(image_url)
        else "not_exist"
    )

    logger.info("rendering dashboard.html..")
    return render_template(
        "dashboard.html",
        pipeline=pipeline,
        user_folder=user_folder,
        deployment_list=deployment_list,
        image_url=image_url,
        content_url=content_url,
        heading=heading,
    )


@app.route("/<path:file_url>", methods=["GET"])
@logged_in
def solution_description(file_url):
    try:
        # check only for last url segment
        last = file_url.split("/")[-1]
        if last in [
            "solution_description.html",
            "solution_icon.png",
            "execution_run.json",
        ]:
            # we construct the path ourselves to prevent malicious path acrobatics
            return send_file(
                os.path.join(
                    pathSolutions,
                    session.get("username"),
                    get_current_deployment_id(),
                    last,
                )
            )

    except Exception as e:
        pass

    response = app.response_class(response=f"file not found {file_url}", status=404)
    return response


@app.route("/upload_execution_data", methods=["POST"])
@logged_in
def upload_execution_data():
    try:

        federation_endpoint_path = os.path.join(
            pathSolutions,
            session.get("username"),
            get_current_deployment_id(),
            "source_system_url.txt",
        )  # get federation api
        execution_run_path = os.path.join(
            pathSolutions,
            session.get("username"),
            get_current_deployment_id(),
            "execution_run.json",
        )  # get execution_run.json path
        blueprint_path = os.path.join(
            pathSolutions,
            session.get("username"),
            get_current_deployment_id(),
            "blueprint.json",
        )  # get blueprint.json path

        if Path(federation_endpoint_path).is_file():
            logger.info(f"{federation_endpoint_path} exists.")
            with open(federation_endpoint_path, "r") as endpoint:
                federation_endpoint_url = (
                    endpoint.read().strip()
                )  # Read and strip any surrounding whitespace
                source_system = (
                    federation_endpoint_url.split("/")[0]
                    + "//"
                    + federation_endpoint_url.split("/")[2]
                )  # source sytem path to indicate the user at the end where to check the file location
                print(f"URL found in file: {federation_endpoint_url}")

            if Path(execution_run_path).is_file() and Path(blueprint_path).is_file():
                logger.info(f"{execution_run_path} exists.")
                with open(execution_run_path, "rb") as execution_run_file, open(
                    blueprint_path, "r"
                ) as blueprint_file:
                    execution_run_content = execution_run_file.read()
                    blueprint_content = json.load(blueprint_file)

                headers = {
                    "Content-Type": "application/octet-stream",
                    "accept": "application/json",
                }

                apiToken = next(
                    (
                        federation_api[api_key]
                        for federation_api in ai_builder_federation_services
                        for api_key in federation_api
                        if api_key == str(federation_endpoint_url)
                    ),
                    None,
                )

                params = {
                    "fullId": str(blueprint_content["pipeline_id"]),
                    "origin": str(blueprint_content["pipeline_id"]),
                    "apiToken": apiToken,
                }

                # we use requests instead of send_file () because we post it to another server
                response = requests.post(
                    os.path.join(federation_endpoint_url, "set_execution_run_data"),
                    headers=headers,
                    params=params,
                    data=execution_run_content,
                )
                if response.status_code == 200:
                    logger.info("File uploaded successfully.")
                    logger.info(f"Response: {response.text}")
                    flash(f"File uploaded successfully!", "success")

                else:
                    logger.info(
                        f"Failed to upload file. Status code: {response.status_code}"
                    )
                    logger.info(f"Response: {response.text}")
                    flash("Failed to upload file.", "danger")

            else:
                logger.info(
                    f"The file to be uploaded does not exist: {execution_run_path}"
                )

        else:
            logger.info(f"{federation_endpoint_path} does not exist.")

    except Exception as e:
        pass

    return redirect(url_for("dashboard", system_url=source_system))


@app.route("/reset", methods=["GET", "POST"])
@logged_in
def reset():
    logger.info("Reset Deployment..")
    # Check if the HTTP request method is 'POST', indicating a form submission
    if request.method == "POST":
        checkbox1 = request.form.get("checkbox1")
        action = request.form.get("action")

        # Determine whether to reset PVC based on the 'checkbox1' value
        reset_value = checkbox1 == "on"
        logger.info("Reset PVC" if reset_value else "No PVC reset")

        # Check the value of the 'action' parameter and perform corresponding actions
        if action == "Submit":
            if "current_deployment_id" in session:
                pipeline = pm.get_pipeline(
                    user_name=session.get("username"),
                    pipeline_id=session.get("current_deployment_id"),
                )
                pipeline.reset_pipeline(reset_pvc=reset_value)
                session["refresh"] = [3, 3]
                logger.info("Reset Deployment successful.")

        elif action == "Cancel":
            logger.info("Reset Deployment Cancelled")

    return redirect("/dashboard")


@app.route("/capture_execution_data", methods=["GET"])
@logged_in
def capture_execution_data():
    logger.info("capture_execution_data..")
    # Check if the HTTP request method is 'POST', indicating a form submission
    if "current_deployment_id" in session:
        pipeline = pm.get_pipeline(
            user_name=session.get("username"),
            pipeline_id=session.get("current_deployment_id"),
        )
        pipeline.save_execution_run()

    return redirect("/dashboard")


def _remove_pipeline(pipeline_id):
    pipeline = pm.get_pipeline(
        user_name=session.get("username"), pipeline_id=pipeline_id
    )
    pipeline.remove_pipeline()


@app.route("/delete", methods=["GET"])
@logged_in
def delete():
    logger.info("Delete Deployments")
    if "current_deployment_id" in session:
        _remove_pipeline(pipeline_id=session.get("current_deployment_id"))
        session.pop("current_deployment_id")

    return redirect("/")  # redirect to home page with message


@app.route("/logs/", methods=["GET"])
@app.route("/pipeline_logs/", methods=["GET"])
@logged_in
def logs():
    pipeline = pm.get_pipeline(
        user_name=session.get("username"),
        pipeline_id=session.get("current_deployment_id"),
    )
    try:
        pod_name = request.args.get("pod_name")
        if pod_name is None:
            abort(400, "Required: pod_name")

        if "current_deployment_id" in session:
            logs = pipeline._get_node_manager().get_logs(pod_name=pod_name).split("\n")
    except Exception as e:
        logger.info(f"exception in displaying logs: {str(e)}")
        if "current_deployment_id" in session:
            logs = pipeline.get_pipeline_logs().split("\n")
    return render_template("logs.html", text=logs)


@app.route("/status_details/", methods=["GET"])
@logged_in
def status_details():
    pipeline = pm.get_pipeline(
        user_name=session.get("username"),
        pipeline_id=session.get("current_deployment_id"),
    )
    try:
        pod_name = request.args.get("pod_name")
        if pod_name is None:
            abort(400, "Required: pod_name")

        if "current_deployment_id" in session:
            logs = (
                pipeline._get_node_manager()
                .get_status_details(pod_name=pod_name)
                .split("\n")
            )

        return render_template("logs.html", text=logs)
    except Exception as e:
        logger.info(f"exception in displaying status_details: {str(e)}")
        response = app.response_class(
            response=f"displaying status_details failed with: {str(e)}", status=500
        )
        return response


@app.route("/shared_folder/", methods=["GET"])
@logged_in
def dir_listing():
    req_path = request.args.get("path", default="", type=str)
    pipeline = pm.get_pipeline(
        user_name=session.get("username"),
        pipeline_id=session.get("current_deployment_id"),
    )
    BASE_DIR = pipeline.get_shared_folder_path()
    print(f"BASE_DIR = {BASE_DIR}")

    if not req_path == "":
        req_path = req_path.lstrip("/")
    abs_path = os.path.join(BASE_DIR, req_path)

    if (not os.path.exists(abs_path)) or (".." in req_path):
        return abort(404)

        # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

        # Show directory contents
    files = [os.path.join(req_path, file) for file in os.listdir(abs_path)]
    return render_template("files.html", files=files)


@app.route("/run", methods=["GET"])
@logged_in
def run():
    pipeline = pm.get_pipeline(
        user_name=session.get("username"),
        pipeline_id=session.get("current_deployment_id"),
    )
    if pipeline.is_running():
        logger.info(f"Pipeline Run already active")
    else:
        pipeline.run_orchestrator_client()
    session["refresh"] = [3, 3, 3, 3, 3]

    return redirect("/dashboard")  # redirect to home page with message


@app.route("/stop-orchestration", methods=["GET"])
@logged_in
def stop_orchestration():
    pipeline = pm.get_pipeline(
        user_name=session.get("username"),
        pipeline_id=session.get("current_deployment_id"),
    )
    pipeline.stop_orchestration()

    return redirect("/dashboard")


def decode_and_write_solution_zip(data, username):
    directory_solution_zip = pathSolutionZips + username
    os.makedirs(directory_solution_zip, exist_ok=True)
    path_solution_zip = f"{directory_solution_zip}/solution.zip"
    filedata = base64.b64decode(data)
    with open(path_solution_zip, "wb+") as f:
        f.write(filedata)
    logger.info(f"solution.zip successfully added to {directory_solution_zip}")
    return directory_solution_zip


def is_allowed_client(client):
    try:
        with open("config.json") as f:
            data = json.load(f)
        allowed_clients = data["allowed_ip_addresses"]

        return client in allowed_clients
    except Exception as e:
        raise Exception(
            "\n -> config.json for allowed_ip_addresses could not be found! "
        ) from e


@app.route("/deploy_solution", methods=["POST"])
def deploy_solution():
    body = {}
    logger.info("enter deploy_solution")
    try:
        body = request.get_json(force=True)
        logger.info("got json")
        client = request.remote_addr
        if not is_allowed_client(client):
            response = app.response_class(
                response=f"Not allowed for your domain: {client}", status=401
            )
            return response

        required = ("solution", "username")
        if not all([r in body.keys() for r in required]):
            abort(400, "Required:" + ", ".join(required))

        username = hexlify(body["username"].lower().strip().encode()).decode("utf-8")
        logger.info(f"got solution and username: {username}")
        directory_solution_zip = decode_and_write_solution_zip(
            body["solution"], username
        )
        pipeline_id = pm.create_pipeline(
            username,
            directory_solution_zip,
            path_kubernetes_pull_secret=app.config["path_kubernetes_pull_secret"],
            name_kubernetes_pull_secret=app.config["name_kubernetes_pull_secret"],
        )
        response = app.response_class(
            response=f"/dashboard?selected_deployment_id={pipeline_id}", status=200
        )
        return response
    except subprocess.CalledProcessError as cpe:
        logger.info(f"exception in deploy_solution: {str(cpe)}")
        logger.error(cpe, stack_info=True)
        response = app.response_class(
            response=f"deploy solution failed with: {str(cpe)}\n\n {cpe.stdout}\n\n {cpe.stderr}",
            status=500,
        )
        return response
    except Exception as e:
        logger.info(f"exception in deploy_solution: {str(e)}")
        logger.error(e, stack_info=True)
        response = app.response_class(
            response=f"deploy solution failed with: {str(e)}", status=500
        )
        return response
