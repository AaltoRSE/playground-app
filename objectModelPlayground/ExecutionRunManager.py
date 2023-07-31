import subprocess
import logging
import json

logger = logging.getLogger(__name__)

''' The class ExecutionRunManager is responsible for requesting information and handling the command in the kubernetes environment'''

class ExecutionRunManager:

    def __init__(self):
       print('')

    def run_kubectl(self,command):          # The function runs the kubectl command passed as an argument
        output=""
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True, text=True, universal_newlines=True)
            output = result.stdout.strip()
            return output
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing command: {command}")
            logger.error(e.stderr)
            return None

    def get_system_info(self):                # The function requests the system info. the function obtains a dict from the run_kubectl() and then iterates over to get the system-info.
        
        system_info ={} 
        cluster_output = self.run_kubectl('kubectl get nodes -o json')
        data=json.loads(cluster_output)
        
        if not cluster_output:
           logger.error('Error in obtaining cluster_output')

        try:
            item = data.get("items", [])
            if item:
                status = item[0].get("status", {})
                system_info["system_name"] = status.get("addresses", [])[1].get("address", "")
                system_info["fqdn"] = status.get("addresses", [])[0].get("address", "")
                system_info["cpu"] = status.get("capacity", {}).get("cpu", "")
                system_info["gpu"] = status.get("allocatable", {}).get("gpu", "")
                system_info["memory"] = status.get("capacity", {}).get("memory", "")
        except:
            logger.error('Error in getting system_info')
            return {}
    
        return system_info

    def get_checksum(self,image):               # The function requests the checksum ( ImageID ) 
      
      checksum = self.run_kubectl(f"kubectl get pods --all-namespaces -o json | jq -r '.items[] | select(.spec.containers[].image | contains(\"{image}\")).status.containerStatuses[].imageID' ")
      return checksum

   
