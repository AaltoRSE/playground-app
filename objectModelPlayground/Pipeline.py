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
from objectModelPlayground.kubernetesClientScriptPlayground import run_kubernetes_client
import objectModelPlayground.OrchestratorClient as OrchestratorClient
import objectModelPlayground.ObjectModelUtils as omUtils
import objectModelPlayground.status_client as status_client
import logging
logging.basicConfig(level=logging.INFO)


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

    def get_shared_folder_status(self):
        if not self.__has_shared_folder():
            return None

        return bool(self._get_pvc())

    def get_shared_folder_path(self):
        if not self.__has_shared_folder():
            return None
        pvc = self._get_pvc()
        cmd = f"kubectl get pv {pvc} -o json"

        out = self._runcmd(cmd)
        out_json = json.loads(out)
        pvc_path = out_json["spec"]["hostPath"]["path"]

        return pvc_path

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
        orchestrator = self.get_orchestrator()
        self._update_pods_information(podsInformation, orchestrator)

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

    # def restartDeployments(self):
    #     with open(self.getPathLogs(),"a") as log_output:
    #         log_output.write("--------------------------------\n")
    #         log_output.write("Logs restartDeployments()\n")
    #     self.__rolloutRestartDeployments()

    # def restartDeployment(self, deployment_name):
    #     self.__rolloutRestartDeployment(deployment_name)

    def remove_pipeline(self):
        self.logger.info("removePipeline()..")
        try:
            self.__remove_path_solution_user_pipeline()
        except Exception as e:
            print(e)
        pipeline_thread = threading.Thread(target=self.__delete_namespace, args=())
        pipeline_thread.start()

    def _is_running(self, timeout_seconds=100):
        self.__wait_until_ready(timeout_seconds)

        host_ip = self._get_node_manager().get_host_ip()
        port = self.get_orchestrator().get_container_port("orchestrator")
        endpoint = str(host_ip) + ":" + str(port)
        self.logger.info(f"endpoint: {endpoint}")
        return status_client.is_running(endpoint=endpoint)

    def _get_node_manager(self):
        return NodeManager(self.__get_namespace())

    def _update_pods_information(self, pods_information, orchestrator):
        for pod in pods_information:
            try:
                port_web_ui = self._get_web_ui_port(orchestrator=orchestrator, pod=pod)
                if port_web_ui is None:
                    pod["Web-UI"] = None
                else:
                    pod["Web-UI"] = f"{pod.pop('hostIP')}:{port_web_ui}"
                    self.logger.info(f"WebUI for pod: {pod['Nodename']} is:")
                    self.logger.info(pod["Web-UI"])
            except Exception as e:
                print(e)
                self.logger.info(f"No WebUI available for pod: {pod['Nodename']}")
                pod["Web-UI"] = None

    def _get_web_ui_port(self, orchestrator, pod):
        container_name = pod["Nodename"]
        self.logger.info("orchestrator.get_container_port()")
        port_container = orchestrator.get_container_port(container_name)
        if port_container is None:
            raise Exception("portContainer == None")

        self.logger.info("orchestrator.get_container_port() done")
        self.logger.info(f"portContainer = {port_container}")

        print("pod['hostIP']: ", pod["hostIP"])
        host_ip = pod["hostIP"]
        webui_port = port_container+1
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.connect((host_ip, webui_port))
        # connection successful
        return str(webui_port)

    def _get_pvc(self):
        cmd = f"kubectl -n {self.__namespace} get pvc"
        out = self._runcmd(cmd)     
        if "No resources found" in out:
            return False
        return out.split()[10]

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
            run_kubernetes_client(namespace=self.__get_namespace(), basepath=self.__get_path_solution_user_pipeline())
            self.__wait_until_ready()
            self._send_protos_to_jupyter()

            self.logger.info("__runKubernetesClientScript() done!")
        except Exception as e:
            self.logger.error("Error in _create_pipeline. Removing it now.")
            self.remove_pipeline()
            raise e

    def __rollout_restart_deployments(self):
        self.logger.info("__rolloutRestartDeployments()..")
        cmd = f"kubectl -n {self.__namespace} rollout restart deployment"
        self.__run_and_log(cmd, "__rolloutRestartDeployments()")
        self.__wait_until_ready(timeout_seconds=10)
        self._send_protos_to_jupyter()

    def _send_protos_to_jupyter(self):
        logging.info("Pipeline._send_proto_to_jupyter() ..")
        
        protofiles_path = self.get_orchestrator().get_protofiles_path()+"/"
        logging.info(f"protofiles_path = {protofiles_path}")
        pod_name_jupyter = self._get_pod_name_jupyter()
        if pod_name_jupyter is None:
            return
        try:
            shared_folder = self.get_orchestrator().get_shared_folder_path()
            logging.info("shared_folder = " + shared_folder)
            
            destination = pod_name_jupyter + ":" + shared_folder + "/microservice/"
        except:
            destination = pod_name_jupyter + ":/home/joyan/microservice"
        logging.info(f"destination = {destination}")
        cmd = f"kubectl -n {self.__namespace} cp {protofiles_path} {destination}"
        self._runcmd(cmd)

    def _get_pod_name_jupyter(self):
        #ToDo Define final image name.
        JUPYTER_IMAGE = "registry.gitlab.cc-asp.fraunhofer.de/recognaize-acumos/jupyter-lab:custom-jupyter"

        image_names, container_names_yaml = self.__get_image_container_names()

        container_name = None
        for image_name, container_name_yaml in zip(image_names, container_names_yaml):
            if JUPYTER_IMAGE in image_name:
                container_name = container_name_yaml
                break
        if container_name is None:
            return None
        pod_names = self._get_node_manager().get_pods_names()
        for pod_name in pod_names:
            self.logger.info(f"name = {pod_name}")
            if container_name in pod_name:
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
    #         ["kubectl", "-n", self.__namespace, "rollout", "restart", "deployment", deployment_name],
    #         check=True)

    def __has_shared_folder(self):
        return self.get_orchestrator().has_shared_folder()

    def __pull_images(self):
        image_names = self.__get_image_names()
        for image_name in image_names:
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
            subprocess.run(["kubectl", "delete", "ns", self.__get_namespace()], check=True)
        except Exception as e:
            self.logger.error(e)

    def __get_path_logs(self):
        return self.__get_path_solution_user_pipeline() + "/logs.txt"

    def __get_image_names(self):
        pathDeploymentsSolution = self.__get_path_solution_user_pipeline() + "/deployments"
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

            self.logger.info("imageName: " + image_name)
            return image_name

    def __get_path_solution_user_pipeline(self):
        return self.__get_path_solution_user() + "/" + self.__get_namespace()

    def __get_path_solution_user(self):
        return self.__path_solutions + "/" + self.__user_name

    def __get_namespace(self):
        return self.__namespace

    def __wait_until_ready(self, timeout_seconds=60):
        self._get_node_manager().wait_until_ready(timeout_seconds)






