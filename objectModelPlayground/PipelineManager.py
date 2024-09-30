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
import os
import logging
import tempfile
import zipfile
import json

from objectModelPlayground.NodeManager import NodeManager
from objectModelPlayground.Pipeline import Pipeline

import objectModelPlayground.ObjectModelUtils as omUtils

logger = logging.getLogger(__name__)


class PipelineManager:
    def __init__(self, pathSolutions, configuration):
        self.pathSolutions = pathSolutions
        self.configuration = configuration
        omUtils.mkdirRecursively(pathSolutions)
        logger.debug(f"{__name__} class initialized")

    def is_healthy(self, username, pipeline_id):
        if pipeline_id is None:
            return False
        pipeline = self.get_pipeline(user_name=username, pipeline_id=pipeline_id)
        return pipeline.is_healthy()

    def remove_all_pipelines(self):
        userNames = self.get_user_names()
        for userName in userNames:
            self.remove_user(userName)

    def remove_user(self, user_name):
        self.__remove_user_pipelines(user_name)
        self.__remove_path_user(user_name)

    def reset_all_pipelines(self):
        user_names = self.get_user_names()
        for user_name in user_names:
            pipeline_ids = self.get_pipeline_ids(user_name)
            for pipeline_id in pipeline_ids:
                pipeline = self.get_pipeline(user_name, pipeline_id)
                pipeline.reset()

    def get_user_names(self):
        user_name = os.listdir(self.pathSolutions)
        return user_name

    def get_pipelines_user(self, user_name):
        pipelines_user = []

        pipeline_ids = self.get_pipeline_ids(user_name)
        for pipeline_id in pipeline_ids:
            pipelines_user.append(self.get_pipeline(user_name, pipeline_id))
        pipelines_user.sort(key=self._get_pipeline_id)
        return pipelines_user

    def get_pipeline_ids_all_users(self):
        user_names = self.get_user_names()
        logging.info(f"user_names={user_names}")
        pipeline_ids = []
        for user_name in user_names:
            pipeline_ids += self.get_pipeline_ids(user_name=user_name)
        return pipeline_ids

    def get_pipeline_ids(self, user_name=None):
        if user_name is None:
            path_solution_names = os.listdir(self.pathSolutions)
            pipeline_ids = []
            for userID in path_solution_names:
                path_solutions = self.pathSolutions + userID
                if not os.path.isdir(path_solutions):
                    continue
                pipeline_ids.extend(os.listdir(path_solutions))
            return pipeline_ids
        else:
            path_solutions = self.pathSolutions + user_name
            if not os.path.isdir(path_solutions):
                return []
            pipeline_ids = os.listdir(path_solutions)
            return pipeline_ids

    def get_pipeline(self, user_name, pipeline_id):
        # TODO Check if pipeline exists
        return Pipeline(
            path_solutions=self.pathSolutions,
            pipeline_id=pipeline_id,
            user_name=user_name,
            config=self.configuration,
        )

    def get_nodes(self, pipeline_id):
        nodes = NodeManager(pipeline_id)
        return nodes

    def create_pipeline(
        self,
        user_name,
        path_solution_zip,
        path_kubernetes_pull_secret=None,
        name_kubernetes_pull_secret=None,
    ):
        self.__create_path_user(user_name)
        logger.info("Folder Created")
        logger.info(f"Sollution.ip : {path_solution_zip}")
        pipeline_name = self.get_pipeline_name(path_solution_zip)
        logger.info(f"Pipeline Name: {pipeline_name}")
        user_pipeline_ids = self.get_pipeline_ids(user_name)
        logger.info(f"User Pipelines: {user_pipeline_ids}")
        all_pipeline_ids = self.get_pipeline_ids()
        logger.info(f"All Pipelines: {all_pipeline_ids}")
        other_pipeline_ids = [
            pid for pid in all_pipeline_ids if pid not in user_pipeline_ids
        ]

        if (
            "unique_deployment_per_solution" in self.configuration
            and self.configuration["unique_deployment_per_solution"]
        ):
            logger.info("Creating unique deployment for solution")
            if pipeline_name in other_pipeline_ids:
                logger.error(
                    f"Pipeline with name {pipeline_name} already exists for a different user. Cannot use the same name twice!"
                )
                return
            if pipeline_name in user_pipeline_ids:
                # Clean up the pipeline and reacreate is.
                self.remove_pipeline(user_name, pipeline_name)

        pipeline = Pipeline(
            path_solutions=self.pathSolutions,
            user_name=user_name,
            path_solution_zip=path_solution_zip,
            path_kubernetes_pull_secret=path_kubernetes_pull_secret,
            name_kubernetes_pull_secret=name_kubernetes_pull_secret,
            config=self.configuration,
        )

        return pipeline.get_pipeline_id()

    def get_pipeline_name(self, path_solution_zip):
        logger.info(f"Getting pipeline name for {path_solution_zip}")
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Temp File created")
            if ".zip" not in path_solution_zip:
                logger.info(f"Solution Zip updated")
                path_solution_zip = path_solution_zip + "/solution.zip"
                logger.info(f"Solution Zip updated")
            with zipfile.ZipFile(path_solution_zip, "r") as zip_ref:
                logger.info(f"Zip file opened")
                zip_ref.extractall(temp_dir)
                logger.info(os.listdir(temp_dir))
                logger.info(
                    f"Zip extracted, loading {os.path.join(temp_dir, 'blueprint.json')}"
                )
                with open(os.path.join(temp_dir, "blueprint.json"), "r") as f:
                    blueprint_json = json.load(f)

                logger.info(
                    f"Blueprint read: {os.path.join(temp_dir, 'blueprint.json')}"
                )
                logger.info(f"Blueprint read")
                return blueprint_json["name"].lower()

    def remove_pipeline(self, user_name, pipeline_id):
        if self.__is_pipeline_existent(user_name, pipeline_id):
            pipeline = Pipeline(
                path_solutions=self.pathSolutions,
                pipeline_id=pipeline_id,
                user_name=user_name,
            )
            pipeline.remove_pipeline()
        else:
            logger.error("User %s does not have pipeline %s", user_name, pipeline_id)
            return

    def _get_pipeline_id(self, pipeline):
        return pipeline.get_pipeline_name()

    def __create_path_user(self, user_name):
        directory = self.pathSolutions + user_name
        omUtils.mkdirRecursively(directory)

    def __remove_user_pipelines(self, user_name):
        pipeline_ids = self.get_pipeline_ids(user_name)
        for pipeline_id in pipeline_ids:
            pipeline = self.get_pipeline(user_name, pipeline_id)
            pipeline.remove_pipeline()

    def __remove_path_user(self, user_name):
        directory = self.pathSolutions + user_name
        try:
            if os.path.exists(directory):
                os.rmdir(directory)
        except OSError as e:
            logger.error(e)

    def __is_pipeline_existent(self, user_name, pipeline_id):
        return pipeline_id in self.get_pipeline_ids(user_name)
