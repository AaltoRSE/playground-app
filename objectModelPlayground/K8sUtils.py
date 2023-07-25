from kubernetes import client, config

class K8sClient:
    _core_instance = None
    _apps_instance = None

    @staticmethod
    def get_core_v1_api():
        if K8sClient._core_instance is None:
            config.load_kube_config()
            K8sClient._core_instance = client.CoreV1Api()
        return K8sClient._core_instance

    @staticmethod
    def get_apps_v1_api():
        if K8sClient._apps_instance is None:
            config.load_kube_config()
            K8sClient._apps_instance = client.AppsV1Api()
        return K8sClient._apps_instance
