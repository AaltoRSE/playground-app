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
import time
import logging
import json
import re
from datetime import datetime, timezone
from kubernetes import client
from concurrent.futures import ThreadPoolExecutor
import ast

from objectModelPlayground.K8sUtils import K8sClient

logger = logging.getLogger(__name__)

class NodeManager:
    def __init__(self, namespace):
        logger.debug(f"{__name__} class initialized")
        self.namespace = namespace

    def get_pods_status(self):
        logger.info("getPodsStatus ..")
        pods = self.__get_pods()
        if len(pods) == 0:
            return 'Not Ready'
        for pod in pods:
            if(self._is_pod_terminating(pod)):
                continue
            if not self.__is_ready(pod):
                return 'Not Ready'
        return 'Ready'

    def get_host_ip(self, pods=None):
        if pods==None:
            pods = self.__get_pods()
        host_ip = self._get_host_ip(pods[0])
        if host_ip is None:
            return "unknownHostIP"
        return host_ip

    def get_pods_names(self):
        pods_names = []
        for pod in self.__get_pods():
            pods_names.append(self._get_pod_name(pod))
        return pods_names

    def get_pods_information(self):
        logger.info("Getting pods information...")
        pods_information = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self._get_pod_info_safe, pod) for pod in self.__get_pods()]
            for future in futures:
                pod_info = future.result()
                if pod_info is not None:
                    pods_information.append(pod_info)

        pods_information.sort(key=lambda x: x["Nodename"])
        return pods_information

    def get_status_details(self, pod_name):
        for pod in self.__get_pods():
            pod_name_tmp = self._get_pod_name(pod)
            logger.info(f"pod_name = {pod_name_tmp}")
            if(self._is_pod_terminating(pod)):
                continue
            logger.info(f"pod Name = {pod_name_tmp}")
            if(pod_name_tmp == pod_name):
                return self._get_status_details(pod)

    def _get_pod_info_safe(self, pod):
        try:
            pod_name = self._get_pod_name(pod=pod)
            if self._is_pod_terminating(pod):
                logger.info(f"Pod {pod_name} is terminating. Skipping.")
                return None
            return self._get_pod_information(pod)
        except Exception as e:
            pod_name = pod_name if 'pod_name' in locals() else 'Unknown'
            logger.error(f"Error getting information for pod {pod_name}: {e}")
            return None

    def wait_until_ready(self, timeout_seconds=120):
        for time_passed in range(timeout_seconds):
            try:
                api_response = K8sClient.get_core_v1_api().list_namespaced_pod(self.namespace, field_selector='status.phase!=Running')
                if len(api_response.items) == 0:
                    return

                logger.info(f"Not running pods: {[pod.metadata.name for pod in api_response.items]}")
                logger.info(f"Namespace {self.namespace} is not ready yet. Waiting {str(time_passed)}/{str(timeout_seconds)} seconds ..")

            except client.exceptions.ApiException as e:
                logger.error(f"Error occurred while getting pods. {str(e)}")
            
            time.sleep(1)
        logger.error(f"Namespace {self.namespace} was not ready after {timeout_seconds} seconds.")

    def _get_pod_information(self, pod):
        try:
            self._check_namespace(pod)
            container_names=self._get_container_names(pod)
            if container_names is None:
                container_name1=None
            else:
                container_name1 = container_names[0]
            host_ip = self._get_host_ip(pod)
            is_ready_container = self.__is_ready(pod)
            pod_name = self._get_pod_name(pod=pod)
            return {"Nodename": container_name1, "hostIP": host_ip,
                    "Status": is_ready_container,
                    "PodName": pod_name}

        except Exception as e:
            logger.error(f"Getting pod information was not possible. Probably containers are not ready yet. Exception raised: {e}")

    def get_logs(self, pod_name):
        try:
            logger.info(f"Retrieving logs for pod '{pod_name}' in namespace '{self.namespace}'..")
            logs = K8sClient.get_core_v1_api().read_namespaced_pod_log(name=pod_name, namespace=self.namespace)
            return(logs)
        except client.exceptions.ApiException as e:
            logger.warning(f"Reading logs for pod {pod_name} was not possible. Probably containers are not ready yet. Exception raised: {e}")

    def _get_dataset_features(self, entry_nodes):
        """
        This function checks if the list of starting nodes is available in existing pods. 
        Further, it reads and finds the logs with the meta key {dataset_features} from the 
        starting nodes and returns the dataset features dictionary.
        """

        feature_dict = {}

        self.wait_until_ready()
        for pod in self.__get_pods():
            pod_name = self._get_pod_name(pod)
            logger.info(f"pod_name = {pod_name}")

            if(self._is_pod_terminating(pod)):
                continue
            logger.info(f"pod Name = {pod_name}")

            for start_node in entry_nodes:
                if start_node in pod_name:
                    log_entry = self.get_logs(pod_name=pod_name) # Read the logs for such nodes
                    dict_pattern = r"{'dataset_features':.*}"
                    match = re.search(dict_pattern, log_entry) # Check if the match is found
   
                    if match:
                        try:
                            dict_str = match.group()
                            feature_dict = ast.literal_eval(dict_str)
                        except (ValueError, SyntaxError) as e:
                            logger.error(f"Error in evaluating dataset string: {e}")

                    if feature_dict:
                        break
        
        return feature_dict, start_node
    
    def _get_metrics_metadata(self):
        """
        This function checks for the nodes containing the metrics. 
        Further, it finds the logs with the meta key {metrics} from the such nodes and returns the metrics dictionary.
        """

        metrics_nodes = []
        metrics_results = {}

        self.wait_until_ready()
        for pod in self.__get_pods():
            pod_name = self._get_pod_name(pod)
            logger.info(f"pod_name = {pod_name}")

            if(self._is_pod_terminating(pod)):
                continue
            logger.info(f"pod Name = {pod_name}")

            initial_log_entry = self.get_logs(pod_name=pod_name)

            initial_dict_pattern = r"MetricsAvailable" # Log entry to scan the nodes with metrics
            if re.search(initial_dict_pattern, initial_log_entry):
                metrics_nodes.append(pod)

        logger.info(f"Nodes containing metrics= {', '.join(node.metadata.name for node in metrics_nodes)}")

        for node in metrics_nodes:
            metrics_dict = {}

            log_entry = self.get_logs(self._get_pod_name(node))
            match = re.search(r"{'metrics':.*}", log_entry) # Log entry to retrieve the nodes with metrics

            if match:
                try:
                    metrics_str = match.group()  # Extract the captured group
                    metrics_dict = ast.literal_eval(metrics_str)
                    metrics_results[node.metadata.name] = metrics_dict       
                except (ValueError, SyntaxError) as e:
                    logger.error(f"Error in evaluating metrics string: {e}")
                    metrics_results[node.metadata.name] = None
            else:
                metrics_results[node.metadata.name] = None
                logger.error("Match not found. Metrics not captured.")

        return metrics_results
           
    def _wait_until_ready(self, pod, timeout_seconds, time_passed=0):
        try:
            pod_name = self._get_pod_name(pod)
            while not self.__is_ready(pod) and time_passed < timeout_seconds:
                logger.info(f"Pipeline {self.namespace} is not ready yet. Waiting for Pod {pod_name}. Waiting {time_passed}/{timeout_seconds} seconds ..")
                time.sleep(1)
                time_passed += 1

            return time_passed
        except Exception as e:
            logger.error(e)

    def _get_host_ip(self, pod):
        try:
            return pod.status.host_ip
        except:
            logger.warning("No host ip found for pod.")
            return None


    def _get_status_details(self, pod):
        try:
            pod_name = self._get_pod_name(pod)
            pod_status = pod.status.phase

            num_ready_containers = len([c for c in pod.status.container_statuses if c.ready])
            num_total_containers = len(pod.spec.containers)
            num_restarts = sum(c.restart_count for c in pod.status.container_statuses)

            create_time = pod.metadata.creation_timestamp
            age = str(datetime.now(timezone.utc) - create_time)

            # Format the information.
            short_status = {
                'name': pod_name,
                'ready': f'{num_ready_containers}/{num_total_containers}',
                'status': pod_status,
                'restarts': num_restarts,
                'age': age
            }
            extensive_status = pod.status.container_statuses

            result = (
                "-------------------------------------------------\n"
                "Short Status: \n\n"
                f"{short_status}\n\n"
                "-------------------------------------------------\n"
                "Extensive Status: \n\n"
                f"{extensive_status}"
            )
            return result
        except Exception as e:
            logger.warning(f"Getting Status Details was not possible. Probably containers are not ready yet. Exception raised: {e}")
            return None
    

    def _get_pod_name(self, pod):
        return pod.metadata.name

    def _get_container_names(self, pod):
        containers = pod.spec.containers
        containerNames = []
        for container in containers:
            containerNames.append(container.name)
        return containerNames

    def _check_namespace(self, pod):
        if (self.namespace != pod.metadata.namespace):
            logger.error("Error checking Namespace! ")
            logger.error("self.namespace = " + self.namespace)
            logger.error("pod.metadata.namespace = " + pod.metadata.namespace)

    def _is_pod_terminating(self, pod):
        pod_name = self._get_pod_name(pod)
        return self.is_pod_terminating(pod_name=pod_name)


    def is_pod_terminating(self, pod_name):
        try:
            api_response = K8sClient.get_core_v1_api().read_namespaced_pod(name=pod_name, namespace=self.namespace)
            return api_response.metadata.deletion_timestamp is not None
        except client.exceptions.ApiException as e:
            print("Exception when calling CoreV1Api->read_namespaced_pod: %s\n" % e)
            return None


    def __is_ready(self, pod):
        pod_name = self._get_pod_name(pod)

        try:
            api_response = K8sClient.get_core_v1_api().read_namespaced_pod(name=pod_name, namespace=self.namespace)
            if api_response.status.phase == 'Running':
                for condition in api_response.status.conditions:
                    if condition.type == "Ready":
                        return condition.status == "True"
            return False

        except client.exceptions.ApiException as e:
            print("Exception when calling CoreV1Api->read_namespaced_pod: %s\n" % e)
            return None

    def __get_pods(self):
        self._pods = K8sClient.get_core_v1_api().list_namespaced_pod(namespace=self.namespace).items
        return self._pods

