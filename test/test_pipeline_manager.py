import unittest
import os



from objectModelPlayground.PipelineManager import PipelineManager
import objectModelPlayground.ObjectModelUtils as omUtils


class PipelineManagerTest(unittest.TestCase):
    pathSolutionsTest = "testsolutions/"
    pathSolutionZip = "../solutionZips/solutionMicroservices"
    pm = PipelineManager(pathSolutionsTest)
    userNameTest = "test-PipelineManager"

    def setUp(self):
        omUtils.mkdirRecursively(self.pathSolutionsTest)

    def tearDown(self):
        self.pm.remove_all_pipelines()
        omUtils.rmdir(self.pathSolutionsTest)

    def _kubernetes_client_script_exists(self, userName, pipeline_id):
        return omUtils.fileExists(self.pathSolutionsTest+userName+"/"+ pipeline_id + "/kubernetes-client-script.py")

    def _namespace_exists(self, userName, pipeline_id):
        pass

    def _user_folder_exists(self, userName):
        return userName in self.pm.get_user_names()

    def _pipeline_folder_exists(self, userName, pipeline_id):
        if(self._user_folder_exists(userName)):
            return pipeline_id in self.pm.get_pipeline_ids(userName)
        return False

    def test_createPipeline(self):
        omUtils.mkdirRecursively(self.pathSolutionsTest)
        pipeline_id = self.pm.create_pipeline(self.userNameTest, self.pathSolutionZip)

        userNames = self.pm.get_user_names()
        self.assertEqual(userNames, [self.userNameTest])
        self.assertEqual(userNames, os.listdir(self.pathSolutionsTest))
        self.assertTrue(self._kubernetes_client_script_exists(self.userNameTest, pipeline_id))

    def test_getInformationPipeline(self):
        pipeline_id = self.pm.create_pipeline(self.userNameTest, self.pathSolutionZip)
        pipeline = self.pm.get_pipeline(self.userNameTest, pipeline_id)
        info = pipeline.get_pods_information()

    def test_removePipelines(self):
        self.pm.remove_all_pipelines()
        userNames = self.pm.get_user_names()
        for userName in userNames:
            pipeline_id = self.pm.get_pipeline_ids(userName)
            self.assertEqual(pipeline_id, [])  # add assertion here
            self.assertEqual(userNames, os.listdir(self.pathSolutionsTest + userName))  # add assertion here

    def test_remove_user(self):
        if self.userNameTest not in self.pm.get_user_names():
            self.pm.create_pipeline(self.userNameTest, self.pathSolutionZip)
        self.assertTrue(os.path.isdir(self.pathSolutionsTest + self.userNameTest))
        self.pm.remove_user(self.userNameTest)
        self.assertFalse(os.path.isdir(self.pathSolutionsTest+"userName"))

    def test_not_none(self):
        # test all information from getpodsinformation not none
        pass

    def test_pods_running(self):
        #ToDo
        # pipeline_id = self.pm.createPipeline(self.userNameTest, self.pathSolutionZip)
        #pods_info = cmd kubectl -n pipeline_id get pods
        # "Running" in pods_info
        pass

if __name__ == '__main__':
    unittest.main()
