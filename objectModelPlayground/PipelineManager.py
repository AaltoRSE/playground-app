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

from objectModelPlayground.NodeManager import NodeManager
from objectModelPlayground.Pipeline import Pipeline

import objectModelPlayground.ObjectModelUtils as omUtils

logger = logging.getLogger(__name__)

class PipelineManager:
    def __init__(self, pathSolutions):
        self.pathSolutions = pathSolutions
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
                pipeline = self.get_pipeline(user_name,pipeline_id)
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

    def get_pipeline_ids(self, user_name):
        path_solutions = self.pathSolutions + user_name
        if not os.path.isdir(path_solutions):
            return []
        pipeline_ids = os.listdir(path_solutions)
        return pipeline_ids


    def get_pipeline(self, user_name, pipeline_id):
        # TODO Check if pipeline exists
        return Pipeline(path_solutions=self.pathSolutions, pipeline_id=pipeline_id, user_name=user_name)

    def get_nodes(self, pipeline_id):
        nodes = NodeManager(pipeline_id)
        return nodes

    def create_pipeline(self, user_name, path_solution_zip):
        self.__create_path_user(user_name)
        pipeline = Pipeline(path_solutions=self.pathSolutions, user_name=user_name, path_solution_zip=path_solution_zip)

        return pipeline.get_pipeline_id()

    def remove_pipeline(self, user_name, pipeline_id):
        if(self.__is_pipeline_existent(user_name, pipeline_id)):
            pipeline = Pipeline(path_solutions=self.pathSolutions, pipeline_id=pipeline_id, user_name=user_name)
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