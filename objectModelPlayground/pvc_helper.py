import logging
from kubernetes import client, watch
from objectModelPlayground.K8sUtils import K8sClient

logger = logging.getLogger(__name__)

class PVC:

    def create_pod_spec(pvc_name):
        volume_name = 'mypvc'
        mount_path = '/pvc'
        
        volume_mount = client.V1VolumeMount(
            name=volume_name,
            mount_path=mount_path
        )

        volume = client.V1Volume(
            name=volume_name,
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name)
        )
        
        container = client.V1Container(
            name='temp-container',
            image='busybox',
            image_pull_policy='IfNotPresent',
            volume_mounts=[volume_mount],
            command=["sh", "-c", f"rm -rf {mount_path}/*"]
        )
        
        return client.V1PodSpec(
            volumes=[volume],
            containers=[container],
            restart_policy='Never'
        )
        
    def create_and_watch_pod(namespace, pvc_name):
        pod_name = 'temp-pod'
        metadata = client.V1ObjectMeta(
            name=pod_name,
            namespace=namespace
        )
        pod_spec = PVC.create_pod_spec(pvc_name)
        pod = client.V1Pod(metadata=metadata, spec=pod_spec)
        
        K8sClient.get_core_v1_api().create_namespaced_pod(namespace=namespace, body=pod)
        
        w = watch.Watch()
        for event in w.stream(K8sClient.get_core_v1_api().list_namespaced_pod, namespace=namespace):
            event_pod_name = event['object'].metadata.name
            pod_status = event['object'].status.phase

            if event_pod_name == pod_name:
                logger.info(f"Pod {event_pod_name} is {pod_status}")
                if pod_status == 'Succeeded' or pod_status == 'Failed':
                    w.stop()
                    logger.info(f"Deleting Pod {event_pod_name}")
                    K8sClient.get_core_v1_api().delete_namespaced_pod(event_pod_name, namespace)
                    break

    def delete_pvc_contents(namespace, pvc_name):
        logger.info(f"Deleting pvc {pvc_name} from namespace = {namespace}")
        PVC.create_and_watch_pod(namespace, pvc_name)
