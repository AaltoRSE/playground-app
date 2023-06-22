import re
from kubernetes import client, config


from objectModelPlayground.PipelineManager import PipelineManager
class NamespaceManager:
    def __init__(self):
        config.load_kube_config()
        self.v1 = client.CoreV1Api()

    def _get_matching_namespaces(self, regex):
        namespaces = self.v1.list_namespace().items
        pattern = re.compile(regex)
        return [ns.metadata.name for ns in namespaces if pattern.search(ns.metadata.name)]

    def delete_namespace(self, namespace_name):
        try:
            api_response = self.v1.delete_namespace(name=namespace_name)
            print("Namespace deleted. status='%s'" % str(api_response.status))
        except client.exceptions.ApiException as e:
            print("Exception when calling CoreV1Api->delete_namespace: %s\n" % e)

    def delete_namespaces(self, namespace_names):
        print("Namespaces to be deleted:")
        print(namespace_names)

        confirm = input("\nDo you really want to delete these namespaces? (yes/no): ")
        if confirm.lower() == 'yes':
            for ns in namespace_names:
                print(f"Deleting namespace {ns}.")
                self.delete_namespace(ns)
        else:
            print("Operation cancelled.")

    def delete_namespaces_regex(self, regex):
        matching_namespaces = self._get_matching_namespaces(regex=regex)
        print(matching_namespaces)

        if matching_namespaces:
            self.delete_namespaces(namespace_names=matching_namespaces)
        else:
            print("No matching namespaces found.")

    def delete_namespaces_solutions(self):
        # Get all namespaces by considering solution_folders
        pathSolutions = "solutions/"
        pm = PipelineManager(pathSolutions)
        pipeline_ids = pm.get_pipeline_ids_all_users()

        self.delete_namespaces(namespace_names=pipeline_ids)

nm = NamespaceManager()
nm.delete_namespaces_solutions()

# REGEX_ALL_PLAYGROUND_NAMESPACES = '.*-[0-9a-f]{32}$'
# nm.delete_namespaces_regex(REGEX_ALL_PLAYGROUND_NAMESPACES)

