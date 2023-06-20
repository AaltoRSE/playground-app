import re
from kubernetes import client, config


class NamespaceManager:
    def __init__(self):
        config.load_kube_config()
        self.v1 = client.CoreV1Api()

    def delete_namespace(self, namespace_name):
        try:
            api_response = self.v1.delete_namespace(name=namespace_name)
            print("Namespace deleted. status='%s'" % str(api_response.status))
        except client.exceptions.ApiException as e:
            print("Exception when calling CoreV1Api->delete_namespace: %s\n" % e)

    def get_matching_namespaces(self, regex):
        namespaces = self.v1.list_namespace().items
        matching_namespaces = []
        pattern = re.compile(regex)
        return [ns.metadata.name for ns in namespaces if pattern.search(ns.metadata.name)]

    def delete_matching_namespaces(self, regex):
        matching_namespaces = self.get_matching_namespaces(regex=regex)
        print(matching_namespaces)

        if matching_namespaces:
            print("Matching namespaces:")
            print(matching_namespaces)
            confirm = input("\nDo you really want to delete these namespaces? (yes/no): ")
            if confirm.lower() == 'yes':
                for ns in matching_namespaces:
                    print(f"Deleting namespace {ns}.")
                    self.delete_namespace(ns)
            else:
                print("Operation cancelled.")
        else:
            print("No matching namespaces found.")


manager = NamespaceManager()
manager.delete_matching_namespaces('.*-[0-9a-f]{32}$')

