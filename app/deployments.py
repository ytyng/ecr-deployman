import datetime
from dataclasses import dataclass

from kubernetes import client

from credentials import CredentialsManager


@dataclass
class Deployment:
    deployment_name: str
    repository_prefix: str
    repository_name: str
    namespace: str
    credential_name: str
    image_tag: str = 'latest'


def process_deployment(
    *, deployment: Deployment,
    credentials_manager: CredentialsManager
):
    """
    デプロイメントの1件の処理
    """
    print(f"Processing deployment: {deployment.deployment_name}")
    # authorize
    credential = credentials_manager.get_credential(deployment.credential_name)
    print(credential)
    credential.update_credential_secret()

    # describe image
    ecr_client = credential.get_ecr_client()
    response = ecr_client.describe_images(
        repositoryName=deployment.repository_name
    )
    # タグでフィルター
    if deployment.image_tag:
        _images = [
            image for image in response['imageDetails']
            if 'latest' in image.get('imageTags', [])]
    else:
        _images = response['imageDetails']

    if not _images:
        print(f"Image not found: {deployment.repository_name}")
        return

    image = _images[0]
    image_pushed_at: datetime.datetime = image['imagePushedAt']

    print(image_pushed_at.isoformat())

    # update deployment
    k8s_client = credential.get_k8s_client()
    v1api = client.AppsV1Api(k8s_client)
    response = v1api.patch_namespaced_deployment(
        name=deployment.deployment_name,
        namespace=deployment.namespace,
        body={
            'spec': {
                'template': {
                    'metadata': {
                        'annotations': {
                            'imageUpdatedAt': image_pushed_at.isoformat()
                        }
                    },
                }
            }
        }
    )
    print(response)
