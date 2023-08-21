import json
import os
import logging

from objectModelPlayground.ExecutionRunManager import ExecutionRunManager
#from ExecutionRunManager import ExecutionRunManager 


logger = logging.getLogger(__name__)

''' The class ExecutionRun is responsible for handling the blueprint.json and creation of execution-run.json inside the solution folder'''

class ExecutionRun:
   def __init__(self, path):
      self.path = path
      self.blueprint_path = path + "/blueprint.json" 
      self.execution_path = path + "/execution_run.json"   
      

   def get_blueprint_json(self):          # The function reads the blueprint.json and get the data, node_list 
      if self.blueprint_path:
         with open(self.blueprint_path,"r") as input_file:
           data=json.load(input_file)
           node_list=data.get("nodes",[])
         
           return data, node_list
      else:
         logger.error('blueprint.json is not found')

   def create_json(self, namespace):                 # The function creates a new execution-run.json, iterates over the data obtained from blueprnt.json
      with open(self.execution_path,"w") as output_file:
         data, node_list = self.get_blueprint_json()
         execution_manager = ExecutionRunManager()

         for node_data in node_list:
            if "image" in node_data:        # If 'image' key is found in the nodelist, it passes the image as arg. to get_checksum() in ExecutionRunManger
               image = node_data["image"]
               node_data["checksum"] = execution_manager.get_checksum(image, namespace)
               logger.info(f'checksum for {image} is generated')
            else:
               logger.info('No image found')
         
         data["system_info"] = execution_manager.get_system_info()        # The 'system_info' key is created and the value is the returned output from get_system_info() in ExcutionRunManager
         json.dump(data, output_file, indent=4)

   def add_dataset_features(self, feature_dict, start_node):
      '''This function adds the dictionary obtained from the Pipeline.py to the execution-run.json.'''
      
      with open(self.execution_path, 'r') as fp:
            data = json.load(fp)

      for node in data['nodes']:
            if node.get("container_name") == start_node:
               node.update(feature_dict)
               break  # Stop after updating the desired node

      with open(self.execution_path, 'w') as fp:
         json.dump(data, fp, indent=4)







