from kubernetes import client, config
import pprint
import logging
logging.basicConfig(level=logging.INFO)

class Service:
    def __init__(self, namespace):
        self.namespace = namespace
        self.logger = logging.getLogger("ObjectModelPlayground.Service")
        self.logger.info("Service class initialized")

    def printServices(self):
        # Configs can be set in Configuration class directly or using helper utility
        services = self.getServices()
        pprint.pprint(services)
    def getServices(self):
        config.load_kube_config()

        v1 = client.CoreV1Api()
        self.logger.info("Service.getServices called")
        ret = v1.list_namespaced_service(namespace=self.namespace)
        self.logger.info("Desired Output: [\"NAME\",\"TYPE\",\"CLUSTER-IP\", \"EXTERNAL-IP\", \"PORT(S)\", \"AGE\"]")
        services = []
        for i in ret.items:
            services.append({"name":i.metadata.name, "Type": i.spec.type, "Cluster IP" : i.spec.cluster_ip, "extIP " : "extIP not available yet", "port(s)" : "PORT(S)", "Age" : "AGE"})
            # print(i.spec.type)

        # Configs can be set in Configuration class directly or using helper utility
        return services
