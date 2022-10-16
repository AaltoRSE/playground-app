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
from objectModelPlayground.PipelineManager import PipelineManager
from objectModelPlayground.Pipeline import Pipeline
import pprint

pathSolutions = "solutions/"
pm = PipelineManager(pathSolutions)

solutionID ="pipelinemicrostr"
userName = "User1"


pathSolutionZips = "../solutionZips/"
pathSolutionZip = pathSolutionZips + solutionID


# pm.removeUser(userName)
pipeline_id = pm.create_pipeline(userName, pathSolutionZip)

# pipeline_id = pm.get_pipeline_ids(userName)[0]
# # print(pipeline_id)
# pipeline = pm.getPipeline(userName, pipeline_id)

# print("pipelineName = ", pipeline.get_pipeline_name())

# podsInformation = pipeline.getPodsInformation()