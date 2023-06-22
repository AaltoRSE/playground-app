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
import shlex
import zipfile
import subprocess
import glob
import threading
import json
import socket
import yaml
from datetime import datetime

from objectModelPlayground.NodeManager import NodeManager
from objectModelPlayground.Orchestrator import Orchestrator
import objectModelPlayground.OrchestratorClient as OrchestratorClient
import objectModelPlayground.ObjectModelUtils as omUtils
import objectModelPlayground.status_client as status_client
import logging
logging.basicConfig(level=logging.INFO)
from kubernetes import client, config


class Pipeline:
    def __init__(self, path_solutions, user_name, path_solution_zip=None, pipeline_id=None):
        self.logger = logging.getLogger("ObjectModelPlayground.Pipeline")

        self.__path_solutions = path_solutions
        self.__user_name = user_name
        self.__path_solution_zip = path_solution_zip

        if pipeline_id is None:
            self.__namespace = self.__create_namespace_name()
            if path_solution_zip is not None:
                self._create_pipeline()
        else:
            self.__namespace = pipeline_id.lower()
        self.logger.info("Pipeline class initialized")
        config.load_kube_config()
        self.v1 = client.CoreV1Api()

    def is_namespace_existent(self):
        namespaces = self.v1.list_namespace().items
        namespaces = [ns.metadata.name for ns in namespaces]
        self.logger.info(namespaces)
        return self.__get_namespace() in namespaces

    def is_healthy(self):
        if not os.path.exists(self.__get_path_solution_user_pipeline()):
            return False
        return self.is_namespace_existent()

    def get_shared_folder_status(self):
        if not self.__has_shared_folder():
            return None

        return bool(self._get_pvc())

    def get_shared_folder_path(self):
        if not self.__has_shared_folder():
            return None
        pvc = self._get_pvc()
        print(pvc)
        
        # Get the corresponding PV for the PVC
        pv = self.v1.read_persistent_volume(name=pvc)
        # print(pv)
        if pv.spec.host_path is not None:
            pvc_path = pv.spec.host_path.path
            print(f"Host path: {pvc_path}")
            return pvc_path
        print("Host path not available for this PV")
        return None

    def get_pipeline_name(self):
        try:
            orchestrator = self.get_orchestrator()
            return orchestrator.get_pipeline_name()
        except Exception as e:
            print(e)
            raise Exception("Error get_pipeline_name. Namespace:", self.__get_namespace()) from e

    def get_pipeline_id(self):
        return self.__get_namespace()

    def get_logs(self):
        return self._get_node_manager().getLogs()

    def get_status(self):
        is_ready = self._get_node_manager().get_pods_status()
        if is_ready == "Not Ready":
            return is_ready
        if not self.is_pipeline():
            return is_ready
        if self._is_running():
            return "Running"
        return is_ready

    def get_pods_information(self):
        nodeManager = self._get_node_manager()
        podsInformation = nodeManager.get_pods_information()
        podsInformation = self._update_pods_information(podsInformation)

        return podsInformation
        
    def get_orchestrator(self):
        return Orchestrator(self.__get_path_solution_user_pipeline())

    def get_pipeline_logs(self):
        with open(self.__get_path_logs(), "r") as logs:
            return logs.read()

    def run_orchestrator_client(self, timeout_seconds=100):
        self.__wait_until_ready(timeout_seconds)

        if(not self._is_running()):
            self.logger.info("Init orchestrator_client.py ..")
            self._init_run()
        self._observe().join()

    def is_pipeline(self):
        orchestrator = Orchestrator(path_solution=self.__get_path_solution_user_pipeline())
        is_deployment_single_model = orchestrator.is_deployment_single_model()
        if is_deployment_single_model:
            self.logger.info("Deployment is a single model")
            return False
        else:
            self.logger.info("Deployment is a pipeline")
            return True

    def pull_and_rollout(self):
        with open(self.__get_path_logs(),"a") as log_output:
            log_output.write("--------------------------------\n")
            log_output.write("Logs pullAndRollout()\n")
        self.__pull_images()
        self.__rollout_restart_deployments()

    def remove_pipeline(self):
        self.logger.info(f"removePipeline(): {self.__get_namespace()}")
        self.__delete_namespace()
        try:
            self.__remove_path_solution_user_pipeline()
        except Exception as e:
            print(e)

    def _is_running(self, timeout_seconds=100):
        self.__wait_until_ready(timeout_seconds)

        host_ip = self._get_node_manager().get_host_ip()
        port = self.get_orchestrator().get_container_port("orchestrator")
        endpoint = str(host_ip) + ":" + str(port)
        self.logger.info(f"endpoint: {endpoint}")
        return status_client.is_running(endpoint=endpoint)

    def _get_node_manager(self):
        return NodeManager(self.__get_namespace())

    def _update_pods_information(self, pods_information):
        orchestrator = self.get_orchestrator()

        for pod in pods_information:
            try:
                port_web_ui = self._get_web_ui_port(pod=pod)
                if port_web_ui is None:
                    pod["Web-UI"] = None
                else:
                    pod["Web-UI"] = f"{pod.pop('hostIP')}:{port_web_ui}"
                    if(self._is_jupyter(pod["Nodename"])):
                        pod["Web-UI"] = pod["Web-UI"] + "/lab?token=" + self._get_token_jupyter()
                    self.logger.info(f"WebUI for pod: {pod['Nodename']} is:")
                    self.logger.info(pod["Web-UI"])
            except Exception as e:
                print(e)
                self.logger.info(f"No WebUI available for pod: {pod['Nodename']}")
                pod["Web-UI"] = None
        return pods_information

    def _get_web_ui_port(self, pod):
        container_name = pod["Nodename"]
        container_name_web_ui = container_name+"webui"

        cmd = f"kubectl -n {self.__get_namespace()} get svc"
        out = self._runcmd(cmd)     
        lines = out.split("\n")
        for line in lines:
            if container_name_web_ui in line:
                index_tcp = line.rfind("TCP")
                webui_port = int(line[index_tcp-6:index_tcp-1])
        if webui_port is None:
            raise Exception("webui_port == None")




        host_ip = pod["hostIP"]
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            test_socket.connect((host_ip, webui_port))
            # connection successful
            return str(webui_port)
        except Exception as e:
            self.logger.debug(e)
            self.logger.info(f"No WebUI available for pod: {pod['Nodename']}")
            return None

    def _get_pvc(self):
        api_response = self.v1.list_namespaced_persistent_volume_claim(self.__get_namespace())
        pvc = api_response.items[0]
        return pvc.spec.volume_name

    def _get_endpoint_orchestrator(self):
        host_ip = self._get_node_manager().get_host_ip()
        port = self.get_orchestrator().get_container_port("orchestrator")
        return str(host_ip) + ":" + str(port)

    def _runcmd(self, cmd):
        args = shlex.split(cmd)
        process = subprocess.run(args, check=True, capture_output=True, text=True)
        return process.stdout

    #not Threadsafe
    def _create_pipeline(self):
        try:
            self.__create_path_solution_directory()
            self.__extract_solution_zip(self.__get_path_solution_user_pipeline())
            with open(self.__get_path_logs(),"a") as log_output:
                function = "_createPipeline"
                log_output.write(f"===============================================================================")
                log_output.write(f"\n=================== Logs for {function}() {datetime.now()} ===================\n")
                log_output.write(f"===============================================================================")
            self.__pull_images()
            self.__create_namespace()
            self.logger.info("__runKubernetesClientScript()..")
            self.__run_kubernetes_client_script()
            self.__run_jupyter_deployment_script()

            self.logger.info("__runKubernetesClientScript() done!")
        except Exception as e:
            self.logger.error("Error in _create_pipeline. Removing it now.")
            self.remove_pipeline()
            raise e

    def __rollout_restart_deployments(self):
        self.logger.info("__rolloutRestartDeployments()..")
        cmd = f"kubectl -n {self.__get_namespace()} rollout restart deployment"
        self.__run_and_log(cmd, "__rolloutRestartDeployments()")
        self.__wait_until_ready(timeout_seconds=10)


    def _get_token_jupyter(self):
        self.logger.info("_get_token_jupyter()")
        self.__wait_until_ready()
        pod_name_jupyter = self._get_pod_name_jupyter()

        if pod_name_jupyter is None:
            return
        try:
            self.logger.info("_get_token_jupyter(). Get Logs.. ")
            logs = self._get_node_manager().get_logs(pod_name_jupyter)

            logs = logs.split("\n")
            token_search_string = "ServerApp]  or http://127.0.0.1:8062/lab?token="
            for log in logs:
                if(token_search_string in log):
                    token = log.split(token_search_string)[1]

            return token
        except:
            return ""

    def _is_jupyter(self, node_name):
        pod_name_jupyter = self._get_pod_name_jupyter()
        if pod_name_jupyter is None:
            return False
        return node_name in pod_name_jupyter

    def _get_pod_name_jupyter(self):
        #ToDo Define final image name.
        self.logger.info("_get_pod_name_jupyter()")
        JUPYTER_IMAGES = ["registry.gitlab.cc-asp.fraunhofer.de/recognaize-acumos/jupyter-connect:latest", \
                          "hub.cc-asp.fraunhofer.de/recognaize-acumos/jupyter-connect", "hub.cc-asp.fraunhofer.de/recognaize-acumos/jupyter-connect:latest"]

        image_names, container_names_yaml = self.__get_image_container_names()

        container_name = None
        for image_name, container_name_yaml in zip(image_names, container_names_yaml):
            if image_name in JUPYTER_IMAGES:
                container_name = container_name_yaml
                self.logger.info(f"Jupyter Image = {image_name}")
                break
        if container_name is None:
            return None
        pod_names = self._get_node_manager().get_pods_names()
        for pod_name in pod_names:
            self.logger.info(f"name = {pod_name}")
            if container_name in pod_name:
                if(self._get_node_manager().is_pod_terminating(pod_name)):
                    continue
                self.logger.info(f"pod_name = {pod_name} \n\n\n")
                return pod_name
        self.logger.error("error in Pipeline._get_pod_name_jupyter()!!")
        return None

    def __get_image_container_names(self):
        image_names = []
        container_names = []
        yaml_files = self.get_orchestrator().get_yamls()
        for yaml_file in yaml_files:
            with open(yaml_file, "r") as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
            try:
                containers = data["spec"]["template"]["spec"]["containers"]
                for container in containers:
                    container_name = container["name"]
                    image_name = container["image"]
                    container_names.append(container_name)
                    image_names.append(image_name)
            except:
                pass
        return image_names, container_names

    def _init_run(self):
        path_solution = self.__get_path_solution_user_pipeline()
        # orchestrator = self.getOrchestrator()
        orchestrator = Orchestrator(path_solution)
        OrchestratorClient.init_run(orchestrator, endpoint=self._get_endpoint_orchestrator())

    def _observe(self):
        return OrchestratorClient.observee(endpoint=self._get_endpoint_orchestrator())

    # def __rolloutRestartDeployment(self, deployment_name):
    #     self.logger.info("__rolloutDeployment() ..")
    #     subprocess.run(
    #         ["kubectl", "-n", self.__get_namespace(), "rollout", "restart", "deployment", deployment_name],
    #         check=True)

    def __has_shared_folder(self):
        return self.get_orchestrator().has_shared_folder()

    def __run_kubernetes_client_script(self):
        namespace = self.__get_namespace()

        base_path = self.__get_path_solution_user_pipeline()
        script = os.path.join(base_path,"kubernetes-client-script.py")
        omUtils.makeFileExecutable(script)

        with open(self.__get_path_logs(),"a") as log_output:
            function = "__run_kubernetes_client_script"
            log_output.write(f"\n=================== {function}() {datetime.now()} ===================\n")

        flags = " -n " + namespace + " -bp "+ base_path + " --image_pull_policy IfNotPresent "
        cmd = "python3 " + script + flags
        with open(self.__get_path_logs(),"a") as log_output:
            args = shlex.split(cmd)
            subprocess.run(args, check=True, stdout=log_output)

    def __run_jupyter_deployment_script(self):
        namespace = self.__get_namespace()
        logging.info(f"namespace {namespace}")
        base_path = self.__get_path_solution_user_pipeline()
        script = os.path.join(base_path,"jupyter-deployment-script.py")
        logging.info(f"namespace {namespace}")
        if(not os.path.exists(script)):
            return

        omUtils.makeFileExecutable(script)

        with open(self.__get_path_logs(),"a") as log_output:
            function = "__run_jupyter_deployment_script"
            log_output.write(f"\n=================== {function}() {datetime.now()} ===================\n")

        flags = " -n " + namespace + " -bp "+ base_path + " "
        cmd = "python3 " + script + flags
        self.__wait_until_ready()
        with open(self.__get_path_logs(),"a") as log_output:
            args = shlex.split(cmd)
            subprocess.run(args, check=True, stdout=log_output)

    def __pull_images(self):
        image_names = self.__get_image_names()
        for image_name in image_names:
            self.logger.info(f"pulling image {image_name} ..")
            self.__docker_pull(image_name)

    def __docker_pull(self, image):
        cmd = "docker pull " + image
        self.__run_and_log(cmd, "__dockerPull")

    def __create_namespace(self):
        subprocess.run(["kubectl", "create", "ns", self.__get_namespace()], check=True)

    def __create_path_solution_directory(self):
        os.mkdir(self.__get_path_solution_user_pipeline())

    # To get the pipeline name from blueprint.json, one first needs to extract the solution.zip to some intermediate folder and look into the blueprint there..
    def __create_namespace_name(self):
        self.logger.info("Creating namespace name by temporarily extracting the solution.zip..")
        path_solution_tmp = self.__get_path_solution_user()+"/tmp"
        self.__extract_solution_zip(path_solution_tmp)

        try:
            orchestrator = Orchestrator(path_solution_tmp)
            namespace_name = orchestrator.get_pipeline_name().lower() + "-" + omUtils.getUUID4()
            self.__remove_path_solution(path_solution_tmp)
            self.logger.info("Creating namespace name done.")
            return namespace_name
        except Exception as e:
            self.__remove_path_solution(path_solution_tmp)
            raise e
            
    def __run_and_log(self,cmd, function):
        with open(self.__get_path_logs(),"a") as log_output:
            log_output.write(f"\n=================== {function}() {datetime.now()} ===================\n")
        with open(self.__get_path_logs(),"a") as log_output:
            args = shlex.split(cmd)
            subprocess.run(args, check=True, stdout=log_output)

    def __remove_path_solution_user_pipeline(self):
        path_solution = self.__get_path_solution_user_pipeline()
        self.__remove_path_solution(path_solution)

    def __remove_path_solution(self, path_solution):
        try:
            omUtils.rmdir(path_solution)
        except OSError as e:
            self.logger.error("Error: %s : %s" % (path_solution, e.strerror))

    def __extract_solution_zip(self, path_solution_extracted):
        if(".zip" not in self.__path_solution_zip):
            self.__path_solution_zip = self.__path_solution_zip + "/solution.zip"
        with zipfile.ZipFile(self.__path_solution_zip, 'r') as zip_ref:
            zip_ref.extractall(path_solution_extracted)

    def __delete_namespace(self):
        try:
            # Invoke the delete_namespace API.
            api_response = self.v1.delete_namespace(name=self.__get_namespace())
            self.logger.info("Namespace deleted. status='%s'" % str(api_response.status))
        except client.exceptions.ApiException as e:
            self.logger.error("Exception when calling CoreV1Api->delete_namespace: %s\n" % e)

    def __get_path_logs(self):
        return os.path.join(self.__get_path_solution_user_pipeline(), "logs.txt")

    def __get_image_names(self):
        pathDeploymentsSolution = os.path.join(self.__get_path_solution_user_pipeline(), "deployments")
        paths = glob.glob(pathDeploymentsSolution + "/*deployment.yaml")
        image_names = []
        for path in paths:
            image_names.append(self.__get_image_name(path))
        return image_names

    def __get_image_name(self, path):
        with open(path, 'r') as file:
            data = file.read().split(" ")

            search_string = 'image:'
            index_search_string = data.index(search_string)
            image_name = data[index_search_string + 1]
            image_name = image_name.rstrip('\n')

            return image_name

    def __get_path_solution_user_pipeline(self):
        return os.path.join(self.__get_path_solution_user(), self.__get_namespace())

    def __get_path_solution_user(self):
        return os.path.join(self.__path_solutions, self.__user_name)

    def __get_namespace(self):
        return self.__namespace

    def __wait_until_ready(self, timeout_seconds=120):
        self._get_node_manager().wait_until_ready(timeout_seconds)






