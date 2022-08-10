import time
import logging
import subprocess

from kubernetes import client, config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ObjectModelPlayground.NodeManager")


class NodeManager:
    def __init__(self, namespace):
        logger.info("Nodes class initialized")
        self.namespace = namespace

    def get_pods_status(self):
        # what about other states like: running, finished. we need thread-information here
        logger.info("getPodsStatus ..")
        pods = self.__get_pods()
        if len(pods) == 0:
            return 'Not Ready'
        for pod in self.__get_pods():
            if(self._is_terminating(pod)):
                continue
            if not self.__is_ready(pod):
                return 'Not Ready'
        return 'Ready'

    def get_host_ip(self):
        pods = self.__get_pods()
        host_ip = self._get_host_ip(pods[0])
        if host_ip is None:
            return "unknownHostIP"
        return host_ip

    def get_pods_information(self):
        logger.info("getPodsInformation ..")
        pods_information = []
        for pod in self.__get_pods():
            if(self._is_terminating(pod)):
                continue
            pods_information.append(self._get_pod_information(pod))
        return pods_information

    def wait_until_ready(self, timeout_seconds=120):
        for time_passed in range(timeout_seconds):
            process = subprocess.run(
                ["kubectl", "-n", self.namespace, "get", "pods", "--field-selector=status.phase!=Running"],
                check=True, stdout=subprocess.PIPE, universal_newlines=True)
            out = process.stdout
            if len(out) == 0:
                return
            print("out =", out)
            logger.info(f"Pipeline {self.namespace} is not ready yet. Waiting {str(time_passed)}/{str(timeout_seconds)} seconds ..")
            time.sleep(1)

    def _get_pod_information(self, pod):
        logger.info("_getPodInformation ..")

        # podIP = pod.status.pod_ip
        try:
            self._check_namespace(pod)
            logs = self._get_logs(pod)
            container_name1 = self._get_container_names(pod)[0]
            host_ip = self._get_host_ip(pod)
            is_ready_container = self.__is_ready(pod)
            status_details = self._get_status_details(pod, is_ready_container)
            return {"Nodename": container_name1, "hostIP": host_ip,
                    "Logs": logs, "Status": is_ready_container,
                    "Status-details": status_details}
        except Exception as e:
            logger.info("Exception in _getPodInformation")
            logger.info(e)

    def _get_logs(self, pod):
        logger.info("getLogs of pod %s ..", self._get_pod_name(pod))
        if(self._is_broken(pod)):
            return ""

        self._wait_until_ready(pod, 7)
        try:
            process = subprocess.run(['kubectl', '-n', self.namespace, 'logs',
                                     self._get_pod_name(pod)], check=True,
                                     stdout=subprocess.PIPE,
                                     universal_newlines=True, timeout=1)
            logs = process.stdout
            return logs
        except Exception as e:
            logger.info("Exception in _getLogs")
            logger.info(e)
            return ""

    def _is_broken(self, pod):
        name = self._get_pod_name(pod)
        process = subprocess.run(
            ["kubectl", "-n", self.namespace, "get", "pod", name],
            check=True, stdout=subprocess.PIPE, universal_newlines=True)
        out = process.stdout

        brokenstrings = ["ImagePullBackOff", "InvalidImageName", "ErrImagePull"]
        for brokenstring in brokenstrings:
            if brokenstring in out:
                logger.info(f"Status of pod: {brokenstring}")
                return True

        return False

    def _wait_until_ready(self, pod, timeout_seconds, time_passed=0):
        pod_name = self._get_pod_name(pod)
        while ((not self._is_ready_kubectl(pod))
                and (time_passed < timeout_seconds)):
            logger.info(f"Pipeline {self.namespace} is not ready yet. Waiting for Pod {pod_name}. Waiting {str(time_passed)}/{str(timeout_seconds)} seconds ..")
            time_passed += 1
            time.sleep(1)
        return time_passed

    def _get_host_ip(self, pod):
        return pod.status.host_ip

    def _get_status_details(self, pod, is_ready_container):
        # if is_ready_container:
        pod_name = self._get_pod_name(pod)
        process = subprocess.run(
            ["kubectl", "-n", self.namespace, "get", "pod", pod_name],
            check=True, stdout=subprocess.PIPE, universal_newlines=True)

        result = "-------------------------------------------------\n"
        result += "Short Status: \n\n"
        result += str(process.stdout)
        result += "\n\n-------------------------------------------------\n"
        result += "Extensive Status: \n\n"
        result += str(pod.status.container_statuses)
        return result
        # return process.stdout
        # else:
            # return pod.status.container_statuses
    
    # def _getPodMetadataNamespace(self, pod):
    #     return self._getPodMetadata().namespace

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

    def _is_terminating(self, pod):
        name = self._get_pod_name(pod)
        process = subprocess.run(
            ["kubectl", "-n", self.namespace, "get", "pod", name],
            check=True, stdout=subprocess.PIPE, universal_newlines=True)
        out = process.stdout

        if "Terminating" in out:
            logger.info("Status of pod: Terminating")
            return True

        return False

    def _is_ready_kubectl(self, pod):
        name = self._get_pod_name(pod)
        process = subprocess.run(
            ["kubectl", "-n", self.namespace, "get", "pod", name],
            check=True, stdout=subprocess.PIPE, universal_newlines=True)
        out = process.stdout
        # logger.info(f"_isReadyKubectl. out = {out}")

        if "Running" in out and ("1/1" in out or "2/2" in out):
            return True

        logger.info(out)

        return False

    def __get_pods(self):
        config.load_kube_config()
        v1 = client.CoreV1Api()
        # ToDo namespaced_service??
        return v1.list_namespaced_pod(namespace=self.namespace).items

    def __is_ready(self, pod):
        try:
            return "True" == pod.status.conditions[2].status
        except Exception as e:
            print(e)
            return False
