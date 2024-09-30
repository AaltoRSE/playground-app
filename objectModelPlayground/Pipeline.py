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
import time
import socket
import yaml
import logging
import requests
import shutil

from datetime import datetime
import json
from kubernetes import client

from objectModelPlayground.NodeManager import NodeManager
from objectModelPlayground.Orchestrator import Orchestrator
import objectModelPlayground.OrchestratorClient as OrchestratorClient
import objectModelPlayground.ObjectModelUtils as omUtils
import objectModelPlayground.status_client as status_client
from objectModelPlayground.K8sUtils import K8sClient
from objectModelPlayground.ExecutionRun import ExecutionRun
from objectModelPlayground.pvc_helper import PVC

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        path_solutions,
        user_name,
        path_solution_zip=None,
        pipeline_id=None,
        path_kubernetes_pull_secret=None,
        name_kubernetes_pull_secret=None,
        config=None,
    ):

        self.__path_solutions = path_solutions
        self.__user_name = user_name
        self.__path_solution_zip = path_solution_zip
        self.__path_kubernetes_pull_secret = path_kubernetes_pull_secret
        self.__name_kubernetes_pull_secret = name_kubernetes_pull_secret
        self.__config = config
        if pipeline_id is None:
            self.__namespace = self.__create_namespace_name()
            if path_solution_zip is not None:
                self._create_pipeline()
        else:
            self.__namespace = pipeline_id.lower()
        logger.debug(f"{__name__} class initialized")

    def is_namespace_existent(self):
        namespaces = K8sClient.get_core_v1_api().list_namespace().items
        namespaces = [ns.metadata.name for ns in namespaces]
        return self.__get_namespace() in namespaces

    def is_healthy(self):
        if not os.path.exists(self.__get_path_solution_user_pipeline()):
            return False
        return self.is_namespace_existent()

    def get_shared_folder_status(self):
        if not self.__has_shared_folder():
            return None

        return bool(self._get_pvc_volume_name())

    def get_shared_folder_path(self):
        if not self.__has_shared_folder():
            return None
        pvc = self._get_pvc_volume_name()
        print(pvc)

        # Get the corresponding PV for the PVC
        pv = K8sClient.get_core_v1_api().read_persistent_volume(name=pvc)
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
            raise Exception(
                "Error get_pipeline_name. Namespace:", self.__get_namespace()
            ) from e

    def get_pipeline_id(self):
        return self.__get_namespace()

    def get_logs(self, pod_name):
        return self._get_node_manager().get_logs(pod_name=pod_name)

    def get_status_details(self, pod_name):
        return self._get_node_manager().get_status_details(pod_name=pod_name)

    def get_status(self):
        is_ready = self._get_node_manager().get_pods_status()
        if is_ready == "Not Ready":
            return is_ready
        if not self.is_pipeline():
            return is_ready
        if self.is_running():
            return "Running"
        return is_ready

    def get_pods_information(self):
        nodeManager = self._get_node_manager()
        podsInformation = nodeManager.get_pods_information()
        logger.info(podsInformation)
        podsInformation = self._update_pods_information(podsInformation)
        logger.info(podsInformation)
        return podsInformation

    def get_orchestrator(self):
        return Orchestrator(self.__get_path_solution_user_pipeline())

    def get_pipeline_logs(self):
        with open(self.__get_path_logs(), "r") as logs:
            return logs.read()

    def run_orchestrator_client(self, timeout_seconds=100):
        self.__wait_until_ready(timeout_seconds)

        if not self.is_running():
            logger.info("Init orchestrator_client.py ..")
            self._init_run()
        return self._observe()

    def is_pipeline(self):
        orchestrator = Orchestrator(
            path_solution=self.__get_path_solution_user_pipeline()
        )
        is_deployment_single_model = orchestrator.is_deployment_single_model()
        if is_deployment_single_model:
            logger.info("Deployment is a single model")
            return False
        else:
            logger.info("Deployment is a pipeline")
            return True

    def reset_pipeline(self, reset_pvc=False):
        logger.info("reset_pipeline started")
        self.__log_big_function(function="reset_pipeline")
        if reset_pvc:
            self._reset_pvc()
        self.__rollout_restart_deployments()
        os.remove(
            os.path.join(self.__get_path_solution_user_pipeline(), "execution_run.json")
        )

    def has_execution_run_file(self):
        return os.path.exists(
            os.path.join(self.__get_path_solution_user_pipeline(), "execution_run.json")
        )

    def _reset_pvc(self):
        try:
            pvc_name = self._get_pvc_name()
            if not pvc_name:
                raise ValueError("PVC name is not available.")
            namespace = self.__get_namespace()

            PVC.delete_pvc_contents(namespace=namespace, pvc_name=pvc_name)
        except ValueError as e:
            logger.warning(str(e))
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

    def remove_pipeline(self):
        logger.info(f"removePipeline(): {self.__get_namespace()}")
        self.__delete_namespace()
        try:
            self.__remove_path_solution_user_pipeline()
        except Exception as e:
            print(e)

    def is_running(self):
        host_ip = self._get_node_manager().get_host_ip()
        port = self.get_orchestrator().get_container_port("orchestrator")
        endpoint = str(host_ip) + ":" + str(port)
        logger.info(f"endpoint: {endpoint}")
        running = False
        try:
            running = status_client.is_running(endpoint=endpoint)
        except Exception as e:
            print(e)
        return running

    def _get_node_manager(self):
        return NodeManager(self.__get_namespace())

    def _update_pods_information(self, pods_information):
        for pod in pods_information:
            try:
                port_web_ui = self._get_web_ui_port(pod=pod)
                port_web_address = self._get_web_ui_address(pod=pod)
                logger.info(f"port_web_ui: {port_web_ui}")
                logger.info(f"port_web_address: {port_web_address}")
                if port_web_ui is None:
                    logger.info(f"WebUI for pod {pod['Nodename']} is: None")
                    pod["Web-UI"] = None
                else:
                    if (
                        self.__config["unique_deployment_per_solution"]
                        and port_web_address is not None
                    ):
                        logger.info(
                            f"WebUI for pod {pod['Nodename']} is: {port_web_address}"
                        )
                        pod["Web-UI"] = f"{port_web_address}"
                    else:
                        logger.info(
                            f"WebUI for pod {pod['Nodename']} is: {port_web_ui}"
                        )
                        pod["Web-UI"] = f"{pod.pop('hostIP')}:{port_web_ui}"
                    if self._is_jupyter(pod["Nodename"]):
                        pod["Web-UI"] = (
                            pod["Web-UI"] + "/lab?token=" + self._get_token_jupyter()
                        )
                    logger.info(f"WebUI for pod {pod['Nodename']} is: {pod['Web-UI']}")
            except Exception as e:
                print(e)
                logger.error(f"No WebUI available for pod: {pod['Nodename']}")
                pod["Web-UI"] = None
        return pods_information

    def _get_web_ui_port(self, pod):
        container_name = pod["Nodename"]
        service_name = container_name + "webui"

        webui_port = self._get_node_port(service_name=service_name)

        host_ip = pod["hostIP"]

        return str(webui_port) if self.__test_socket(host_ip, webui_port) else None

    def _get_web_ui_address(self, pod):
        container_name = pod["Nodename"]
        service_name = container_name + "webuiingress"
        logger.info(f"trying to retrieve URL for {service_name}")
        webui_url = self._get_ingress_url(service_name=service_name)

        return str(webui_url) if self.__test_url(webui_url) else None

    def _get_ingress_url(self, service_name):
        try:
            api_response = K8sClient.get_networking_v1_api().read_namespaced_ingress(
                name=service_name, namespace=self.__get_namespace()
            )
            rules = api_response.spec.rules
            logger.info(f"URL is: {rules[0].host}")
            return rules[0].host
        except client.exceptions.ApiException as e:
            print("Exception when calling CoreV1Api->read_namespaced_service: %s\n" % e)

    def _get_node_port(self, service_name):
        try:
            api_response = K8sClient.get_core_v1_api().read_namespaced_service(
                name=service_name, namespace=self.__get_namespace()
            )

            for port in api_response.spec.ports:
                if port.node_port is not None:
                    return port.node_port
        except client.exceptions.ApiException as e:
            print("Exception when calling CoreV1Api->read_namespaced_service: %s\n" % e)

    def __test_socket(self, host_ip, webui_port):
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            test_socket.connect((host_ip, webui_port))
            return True
        except Exception:
            return False

    def __test_url(self, web_url):
        """
        Test whether a server is reachable by sending an HTTP GET request to the given URL.

        :param url: The URL of the server.
        :return: True if the server is reachable, False otherwise.
        """
        try:

            response = requests.get(f"https://{web_url}", timeout=5)
            return response.status_code == 200
        except requests.RequestException:

            return False

    def _get_pvc_name(self):
        return self.get_orchestrator().get_pvc_name()

    def _get_pvc_volume_name(self):
        api_response = (
            K8sClient.get_core_v1_api().list_namespaced_persistent_volume_claim(
                self.__get_namespace()
            )
        )
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

    # not Threadsafe
    def _create_pipeline(self):
        try:
            if (
                "unique_deployment_per_solution" in self.__config
                and self.__config["unique_deployment_per_solution"]
            ):
                # Do some cleanup before deploying
                self.__delete_path_solution_directory()
                self.__delete_namespace()

            self.__create_path_solution_directory()
            self.__extract_solution_zip(self.__get_path_solution_user_pipeline())
            self.__log_big_function(function="_createPipeline")
            self.__create_namespace()
            logger.info("__runKubernetesClientScript()..")
            self.__run_kubernetes_client_script()
            self.__run_jupyter_deployment_script()

            logger.info("__runKubernetesClientScript() done!")
        except Exception as e:
            logger.error("Error in _create_pipeline. Removing it now.")
            self.remove_pipeline()
            raise e

    def __rollout_restart_deployment(self, deployment_name):
        api_response = K8sClient.get_apps_v1_api().read_namespaced_deployment(
            deployment_name, self.__get_namespace()
        )

        # Here we add an annotation to force kubernetes to rollout restart
        if api_response.spec.template.metadata.annotations is None:
            api_response.spec.template.metadata.annotations = {}
        api_response.spec.template.metadata.annotations[
            "kubectl.kubernetes.io/restartedAt"
        ] = datetime.utcnow().isoformat()

        K8sClient.get_apps_v1_api().patch_namespaced_deployment(
            deployment_name, self.__get_namespace(), api_response
        )
        self.__log(
            message=f"{deployment_name} restarted",
            function="__rollout_restart_deployment",
        )

    def __rollout_restart_deployments(self):
        logger.info("__rolloutRestartDeployments()..")
        deployments = K8sClient.get_apps_v1_api().list_namespaced_deployment(
            self.__get_namespace()
        )

        for deployment in deployments.items:
            self.__rollout_restart_deployment(deployment_name=deployment.metadata.name)

        self.__wait_until_ready(timeout_seconds=10)

    def _get_token_jupyter(self):
        logger.info("_get_token_jupyter()")
        self.__wait_until_ready()
        pod_name_jupyter = self._get_pod_name_jupyter()

        if pod_name_jupyter is None:
            return
        try:
            logger.info("Get Logs of jupyter pod..")
            logs = self._get_node_manager().get_logs(pod_name_jupyter)

            logs = logs.split("\n")
            token_search_string = "ServerApp]  or http://127.0.0.1:8062/lab?token="
            for log in logs:
                if token_search_string in log:
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
        # ToDo Define final image name.
        logger.debug("_get_pod_name_jupyter()")
        JUPYTER_IMAGES = [
            "registry.gitlab.cc-asp.fraunhofer.de/recognaize-acumos/jupyter-connect:latest",
            "hub.cc-asp.fraunhofer.de/recognaize-acumos/jupyter-connect",
            "hub.cc-asp.fraunhofer.de/recognaize-acumos/jupyter-connect:latest",
        ]

        image_names, container_names_yaml = self.__get_image_container_names()

        container_name = None
        for image_name, container_name_yaml in zip(image_names, container_names_yaml):
            if image_name in JUPYTER_IMAGES:
                container_name = container_name_yaml
                logger.info(f"Jupyter Image = {image_name}")
                break
        if container_name is None:
            return None
        pod_names = self._get_node_manager().get_pods_names()
        for pod_name in pod_names:
            logger.info(f"pod_name = {pod_name}")
            if container_name in pod_name:
                if self._get_node_manager().is_pod_terminating(pod_name):
                    continue
                return pod_name
        logger.error("error in Pipeline._get_pod_name_jupyter()!!")
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
        orchestrator = Orchestrator(path_solution)
        OrchestratorClient.init_run(
            orchestrator, endpoint=self._get_endpoint_orchestrator()
        )

    def save_execution_run(self):
        path_solution = self.__get_path_solution_user_pipeline()
        executionrun = ExecutionRun(path_solution)
        executionrun.create_json(namespace=self.__get_namespace())
        self._get_starting_nodes(path_solution)
        feature_dict, start_node, metrics_results = self._get_metadata()
        executionrun.add_dataset_features(feature_dict, start_node)
        executionrun.add_metrics_features(metrics_results)

    def stop_orchestration(self):
        logging.info("Stopping orchestration..")
        OrchestratorClient.stop_orchestration(
            endpoint=self._get_endpoint_orchestrator()
        )
        logging.info("saving execution_run..")
        self.save_execution_run()
        logging.info("end stop_orchestration()")

    def _get_starting_nodes(self, path_solution):
        """
        This function scans for the entry nodes with 'Empty' as the input message and returns a list.
        For this purpose, we use the blueprint.json file that gives the pipeline's topology.
        """

        self.blueprint_path = path_solution + "/blueprint.json"

        with open(self.blueprint_path) as fp:
            data = json.load(fp)["nodes"]  # Load all the nodes in json file.

            # Extract a list of entry nodes from the blueprint data using the Empty input message.
            self.entry_nodes = [
                node.get("container_name")
                for node in data
                for signature in node.get("operation_signature_list", [])
                if signature.get("operation_signature", {}).get("input_message_name")
                == "Empty"
            ]

        logger.info(
            f"Nodes with 'Empty' as input message (Starting nodes)= {self.entry_nodes}"
        )

        return self.entry_nodes

    def _get_metadata(self):
        """
        This function retrieves the metadata information, such as the dataset features and metrics
        """
        nd = NodeManager(namespace=self.__get_namespace())

        feature_dict, start_node = nd._get_dataset_features(
            self.entry_nodes
        )  # Retrieve the dataset features
        metrics_results = (
            nd._get_metrics_metadata()
        )  # Retrieve the metrics from different nodes

        return feature_dict, start_node, metrics_results

    def _observe(self):
        return OrchestratorClient.observe(
            endpoint=self._get_endpoint_orchestrator(), pipeline=self
        )

    def __has_shared_folder(self):
        return self.get_orchestrator().has_shared_folder()

    def __get_flags_kubernetes_pull_secret(self):
        flags_secret = f" -sn {self.__name_kubernetes_pull_secret} -ps {self.__path_kubernetes_pull_secret} "
        if self.__path_kubernetes_pull_secret is None:
            logger.warning(
                "path_secret is not set. Therefore no ImagePullSecrets can be used to pull images"
            )
            flags_secret = ""
        if self.__name_kubernetes_pull_secret is None:
            logger.warning(
                "name_secret is not set. Therefore no ImagePullSecrets can be used to pull images"
            )
            flags_secret = ""
        return flags_secret

    def __run_kubernetes_client_script(self):
        namespace = self.__get_namespace()

        base_path = self.__get_path_solution_user_pipeline()
        script = os.path.join(base_path, "kubernetes-client-script.py")
        omUtils.makeFileExecutable(script)

        flags_secret = self.__get_flags_kubernetes_pull_secret()
        flags = f" -n {namespace} -bp {base_path} {flags_secret} "
        if flags_secret == "":
            flags += " --image_pull_policy IfNotPresent "
        flags += f" --config-file {os.getcwd()}/config.json "

        cmd = "python3 " + script + flags
        self.__run_and_log(cmd=cmd, function="__run_kubernetes_client_script")

    def __run_jupyter_deployment_script(self):
        namespace = self.__get_namespace()
        base_path = self.__get_path_solution_user_pipeline()
        script = os.path.join(base_path, "jupyter-deployment-script.py")
        if not os.path.exists(script):
            return

        omUtils.makeFileExecutable(script)

        flags = " -n " + namespace + " -bp " + base_path + " "
        cmd = "python3 " + script + flags
        self.__wait_until_ready()
        self.__run_and_log(cmd=cmd, function="__run_jupyter_deployment_script")

    def __create_namespace(self):
        meta = client.models.v1_object_meta.V1ObjectMeta(name=self.__get_namespace())
        body = client.V1Namespace(metadata=meta)

        api_response = K8sClient.get_core_v1_api().create_namespace(body)
        self.__log(
            message=f"Namespace created. status='{api_response.status}'",
            function="__create_namespace",
        )

    def __create_path_solution_directory(self):
        os.mkdir(self.__get_path_solution_user_pipeline())

    def __delete_path_solution_directory(self):
        if os.path.exists(self.__get_path_solution_user_pipeline()):
            shutil.rmtree(self.__get_path_solution_user_pipeline())

    # To get the pipeline name from blueprint.json, one first needs to extract the solution.zip to some intermediate folder and look into the blueprint there..
    def __create_namespace_name(self):
        logger.info(
            "Creating namespace name by temporarily extracting the solution.zip.."
        )
        path_solution_tmp = self.__get_path_solution_user() + "/tmp"
        self.__extract_solution_zip(path_solution_tmp)

        try:
            orchestrator = Orchestrator(path_solution_tmp)
            logger.info(f"{os.listdir(path_solution_tmp)}")
            namespace_name = (
                orchestrator.get_pipeline_name().lower() + "-" + omUtils.getUUID4()
            )
            if (
                "unique_deployment_per_solution" in self.__config
                and self.__config["unique_deployment_per_solution"]
            ):
                logger.info("Unique solution found. Creating namespace.")
                # We clean up any previous and set up a new one.
                namespace_name = orchestrator.get_pipeline_name().lower()
            self.__remove_path_solution(path_solution_tmp)
            logger.info("Creating namespace name done.")
            return namespace_name
        except Exception as e:
            self.__remove_path_solution(path_solution_tmp)
            raise e

    def __run_and_log(self, cmd, function):
        args = shlex.split(cmd)
        try:
            message = subprocess.run(args, capture_output=True, text=True, check=True)
            message = message.stdout + "\n" + message.stderr
            self.__log(message=message, function=function)
        except subprocess.CalledProcessError as cpe:
            message = cpe.stdout + "\n\n" + cpe.stderr
            self.__log(message=message, function=function)
            raise cpe

    def __log(self, message, function):
        with open(self.__get_path_logs(), "a") as log_output:
            log_output.write(
                f"\n=================== {function}() {datetime.now()} ===================\n"
            )
            log_output.write(message)

    def __log_big_function(self, function):
        with open(self.__get_path_logs(), "a") as log_output:
            log_output.write(
                f"\n\n==============================================================================="
            )
            log_output.write(
                f"\n=================== Logs for {function}() {datetime.now()} ===================\n"
            )
            log_output.write(
                f"==============================================================================="
            )

    def __remove_path_solution_user_pipeline(self):
        path_solution = self.__get_path_solution_user_pipeline()
        self.__remove_path_solution(path_solution)

    def __remove_path_solution(self, path_solution):
        try:
            omUtils.rmdir(path_solution)
        except OSError as e:
            logger.error("Error: %s : %s" % (path_solution, e.strerror))

    def __extract_solution_zip(self, path_solution_extracted):
        if ".zip" not in self.__path_solution_zip:
            self.__path_solution_zip = self.__path_solution_zip + "/solution.zip"
        with zipfile.ZipFile(self.__path_solution_zip, "r") as zip_ref:
            zip_ref.extractall(path_solution_extracted)

    def __delete_namespace(self):
        namespace = self.__get_namespace()
        logger.info(f"Deleting namespace: {namespace}")
        try:
            # Invoke the delete_namespace API.
            K8sClient.get_core_v1_api().delete_namespace(name=namespace)
            while True:
                try:
                    logger.info(f"Getting namespace status")
                    ns = K8sClient.get_core_v1_api().read_namespace(name=namespace)
                    logger.info(
                        f"Namespace '{namespace}' is still in phase: {ns.status.phase}"
                    )
                except client.exceptions.ApiException as e:
                    logger.info(f"Exception when checking namespace status: {e}")
                    if e.status == 404:
                        logger.info(f"Namespace '{namespace}' has been deleted.")
                        return
                    else:
                        logger.error(f"Exception when checking namespace status: {e}")
                time.sleep(5)
        except client.exceptions.ApiException as e:
            logger.error("Exception when calling CoreV1Api->delete_namespace: %s\n" % e)

    def __get_path_logs(self):
        return os.path.join(self.__get_path_solution_user_pipeline(), "logs.txt")

    def __get_path_solution_user_pipeline(self):
        return os.path.join(self.__get_path_solution_user(), self.__get_namespace())

    def __get_path_solution_user(self):
        return os.path.join(self.__path_solutions, self.__user_name)

    def __get_namespace(self):
        return self.__namespace

    def __wait_until_ready(self, timeout_seconds=120):
        self._get_node_manager().wait_until_ready(timeout_seconds)
