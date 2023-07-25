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
import logging

from objectModelPlayground.K8sUtils import K8sClient

logger = logging.getLogger(__name__)

class Service:
    def __init__(self, namespace):
        self.namespace = namespace
        logger.debug(f"{__name__} class initialized")

    def getServices(self):

        self.logger.info("Service.getServices called")
        ret = K8sClient.get_core_v1_api().list_namespaced_service(namespace=self.namespace)
        self.logger.info("Desired Output: [\"NAME\",\"TYPE\",\"CLUSTER-IP\", \"EXTERNAL-IP\", \"PORT(S)\", \"AGE\"]")
        services = []
        for i in ret.items:
            services.append({"name":i.metadata.name, "Type": i.spec.type, "Cluster IP" : i.spec.cluster_ip, "extIP " : "extIP not available yet", "port(s)" : "PORT(S)", "Age" : "AGE"})
        return services
