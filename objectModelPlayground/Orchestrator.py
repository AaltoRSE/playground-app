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
import json
import logging
import os
import yaml

import objectModelPlayground.ObjectModelUtils as omUtils
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("ObjectModelPlayground.Orchestrator")
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Orchestrator:
    def __init__(self, path_solution):
        logger.info(f"pathSolution = {path_solution}")
        self.path_solution = path_solution
        self.path_docker_info = path_solution + "/dockerinfo.json"
        self.path_blueprint = path_solution + "/blueprint.json"
        self.deploymentsyamls = path_solution + "/deployments"
        self.path_solution_model_name = path_solution + "/modelname.txt"
        self.path_solution_icon = (path_solution + "/solution_icon.png").replace("//", "/")
        self.path_solution_description = (path_solution + "/solution_description.html").replace("//", "/")

    def has_shared_folder(self):
        return "pvc.yaml" in os.listdir(self.deploymentsyamls)

    def get_pipeline_name(self):
        blueprint_json = self.get_blueprint_json()
        pipeline_name = ""
        if blueprint_json:
            pipeline_name = blueprint_json["name"]
        else:

            pipeline_name = self.get_model_name()

        pipeline_name = pipeline_name.replace(" ", "-")
        pipeline_name = pipeline_name.replace("_", "-")

        return pipeline_name

    def get_blueprint_json(self):
        if not omUtils.fileExists(self.path_blueprint):
            logger.info(f"File {self.path_blueprint} could not be found!")
            return False
            # raise ValueError(f"File {self.pathBlueprint} could not be found!")
        with open(self.path_blueprint) as json_file:
            data = json.load(json_file)
            return data

    def get_model_name(self):
        logger.info("Deployment is a single model. -> getModelName")

        file = self.path_solution_model_name
        return self._readfile(file)

    def get_container_names(self):
        """Get container port."""
        infos_json = self.get_docker_info_json()
        if not infos_json:
            infos_json = self.get_model_name()
        if not infos_json:
            logger.error("Container name could not be found!")
            # raise ValueError("Container name could not be found!")
            return "test"
        names = []
        for info in infos_json:
            names.append(self._get_container_name(info))
        return names

    def get_container_port(self, container_name):
        """Get container port."""
        infos_json = self.get_docker_info_json()
        if not infos_json:
            return None
        for info in infos_json:
            if(self._get_container_name(info) == container_name):
                return info["port"]

    def get_docker_info_json(self):
        """Get docker_info.json."""

        if not omUtils.fileExists(self.path_docker_info):
            return False
        with open(self.path_docker_info, encoding='UTF-8') as json_file:
            data = json.load(json_file)
            data = data["docker_info_list"]
            return data

    def get_blueprint(self):
        """Get blueprint.json."""
        return self._readfile(self.path_blueprint)

    def get_docker_info(self):
        """Get dockerinfo.json."""
        return self._readfile(self.path_docker_info)

    def get_protofiles_path(self):
        return os.path.join(self.path_solution, 'microservice')


    def get_protofiles(self):
        """Get Proto Files in Microservice folder."""
        msd = self.get_protofiles_path()
        protofiles_paths = [
            os.path.join(msd, protofile)
            for protofile in os.listdir(msd)
            if protofile.endswith('.proto')
        ]
        protofiles = {
            os.path.basename(fname): self._readfile(fname)
            for fname in protofiles_paths
        }
        return protofiles

    def is_deployment_single_model(self):
        yamls = self.get_yamls()
        return len(yamls) <= 4

    def get_yamls(self):
        path_yamls = self.path_solution + "/deployments/"
        files = os.listdir(path_yamls)
        files_yaml = [file for file in files if self._is_yaml_file(file)]
        yamls = [path_yamls + file for file in files_yaml]
        if len(yamls) < 4:
            logger.error(f"Only {len(yamls)} yaml files in solution.zip. Should be at least four!")
        return yamls

    def get_shared_folder_path(self):
        logger.info("get_shared_folder_path")
        yaml_files = self.get_yamls()
        logger.info(f"yaml_files = {yaml_files}")
        for yaml_file in yaml_files:
            with open(yaml_file, "r") as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
            try:
                environment_variables = data["spec"]["template"]["spec"]["containers"][0]["env"]
                for environment_variable in environment_variables:
                    if environment_variable["name"] == "SHARED_FOLDER_PATH":
                        shared_folder_path = environment_variable["value"]
                        return shared_folder_path
            except:
                pass

    def _readfile(self, path) -> str:
        if not omUtils.fileExists(path):
            logger.error(f"File {path} could not be found!")
            raise ValueError(f"File {path} could not be found!")
        with open(path, 'rt', encoding='UTF-8') as file:
            return file.read()

    def _get_container_name(self, container_info):
        return container_info["container_name"]

    def _is_yaml_file(self, file):
        return file.endswith(".yaml") or file.endswith("yml")

    def get_solution_icon(self):
        if not omUtils.fileExists(self.path_solution_icon):
            logger.info(f"File {self.path_solution_icon} could not be found!")
            return False
        return self.path_solution_icon

    def get_solution_description(self):
        if not omUtils.fileExists(self.path_solution_description):
            logger.info(f"File {self.path_solution_description} could not be found!")
            return False
        return self.path_solution_description
