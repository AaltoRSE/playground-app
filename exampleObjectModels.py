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