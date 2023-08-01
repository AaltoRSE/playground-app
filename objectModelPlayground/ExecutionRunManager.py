import subprocess
import logging
import json
from kubernetes import client

#from objectModelPlayground.K8sUtils import K8sClient
from K8sUtils import K8sClient

logger = logging.getLogger(__name__)

''' The class ExecutionRunManager is responsible for requesting information and handling the command in the kubernetes environment'''

class ExecutionRunManager:

    def __init__(self):
       print('')

    def get_system_info(self):                # The function requests the system info. the function obtains a dict from the run_kubectl() and then iterates over to get the system-info.
        
        system_info ={} 
        nodes = K8sClient.get_core_v1_api().list_node()

        try:
            for node in nodes.items:            
                system_info["system_name"] = node.metadata.name
                system_info["fqdn"] = node.status.addresses[0].address
                system_info["cpu"] = node.status.capacity.get("cpu","")
                system_info["gpu"] = node.status.capacity.get("gpu","")
                system_info["memory"] = node.status.capacity.get("memory","")
        except:
            logger.error('Error in getting system_info')
            return {}
    
        return system_info

    def get_checksum(self,image):               # The function requests the checksum ( ImageID ) 
      
      pods = K8sClient.get_core_v1_api().list_pod_for_all_namespaces(watch=False)
      for pod in pods.items:
        for container in pod.spec.containers:
            if image in container.image:           
                checksum = pod.status.container_statuses[0].image_id
                return checksum
            
      
      

   
