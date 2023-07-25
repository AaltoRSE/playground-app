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
from datetime import datetime, timezone
from kubernetes import client

from objectModelPlayground.K8sUtils import K8sClient

logger = logging.getLogger("ObjectModelPlayground.NodeManager")


class NodeManager:
    def __init__(self, namespace):
        logger.debug("Nodes class initialized")
        self.namespace = namespace

    def get_pods_status(self):
        # what about other states like: running, finished. we need thread-information here
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


    def get_logs(self, container_name):
        self.wait_until_ready()
        for pod in self.__get_pods():
            pod_name = self._get_pod_name(pod)
            logger.info(f"pod_name = {pod_name}")
            if(self._is_pod_terminating(pod)):
                continue
            logger.info(f"pod Name = {pod_name}")
            if(pod_name == container_name):
                logs = self._get_logs(pod)
                return logs
                

    def get_pods_information(self):
        logger.info("getPodsInformation ..")
        pods_information = []
        for pod in self.__get_pods():
            if(self._is_pod_terminating(pod)):
                continue
            pods_information.append(self._get_pod_information(pod))
        return pods_information

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
        logger.info("_getPodInformation ..")

        # podIP = pod.status.pod_ip
        try:
            self._check_namespace(pod)
            logs = self._get_logs(pod)
            container_name1 = self._get_container_names(pod)[0]
            host_ip = self._get_host_ip(pod)
            is_ready_container = self.__is_ready(pod)
            status_details = self._get_status_details(pod)
            return {"Nodename": container_name1, "hostIP": host_ip,
                    "Logs": logs, "Status": is_ready_container,
                    "Status-details": status_details}
        except Exception as e:
            logger.info("Exception in _getPodInformation")
            logger.info(e)

    def _get_logs(self, pod):
        pod_name = self._get_pod_name(pod)

        if(self._is_broken(pod)):
            logger.warning(f"Pod {pod_name} is broken.")
            return ""

        self._wait_until_ready(pod, timeout_seconds=7)

        try:
            logger.info(f"Retrieving logs for pod '{pod_name}' in namespace '{self.namespace}'..")
            logs = K8sClient.get_core_v1_api().read_namespaced_pod_log(name=pod_name, namespace=self.namespace)
            return(logs)
        except client.exceptions.ApiException as e:
            logger.error("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)

    def _is_broken(self, pod):
        pod_name = self._get_pod_name(pod)
        try:
            api_response = K8sClient.get_core_v1_api().read_namespaced_pod(name=pod_name, namespace=self.namespace)
            for container_status in api_response.status.container_statuses:
                if container_status.state.waiting is not None:
                    logger.info(f"Container {container_status.name} status: {container_status.state.waiting.reason}")
                    return True
                elif container_status.state.running is not None:
                    logger.info(f"Container {container_status.name} is running")
                    return False
                elif container_status.state.terminated is not None:
                    logger.info(f"Container {container_status.name} terminated with reason: {container_status.state.terminated.reason}")
                    return True
        except client.exceptions.ApiException as e:
            logger.error("Exception when calling CoreV1Api->read_namespaced_pod: %s\n" % e)
            return True

    def _wait_until_ready(self, pod, timeout_seconds, time_passed=0):
        pod_name = self._get_pod_name(pod)
        while not self.__is_ready(pod) and time_passed < timeout_seconds:
            logger.info(f"Pipeline {self.namespace} is not ready yet. Waiting for Pod {pod_name}. Waiting {time_passed}/{timeout_seconds} seconds ..")
            time.sleep(1)
            time_passed += 1

        return time_passed

    def _get_host_ip(self, pod):
        return pod.status.host_ip

    def _get_status_details(self, pod):
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

        result = (
            "-------------------------------------------------\n"
            "Short Status: \n\n"
            f"{short_status}\n\n"
            "-------------------------------------------------\n"
            "Extensive Status: \n\n"
            f"{pod.status.container_statuses}"
        )
        return result
    
    def _get_pod_metadata(self, pod):
        return pod.metadata

    def _get_pod_name(self, pod):
        return pod.metadata.name

    def _get_container_names(self, pod):
        containers = pod.spec.containers
        containerNames = []
        for container in containers:
            containerNames.append(container.name)
        return containerNames

    def _get_node_name(self, pod):
        return self._get_image_name(pod).split("/")[-1]

    def _get_image_name(self, pod):
        return pod.spec.containers[0].image

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
            # return api_response.status.phase == 'Running'
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

