import datetime
from dataclasses import dataclass

from credentials import CredentialsManager
from kv_store import AbstractKVStore
from logger import logger

from kubernetes import client


@dataclass
class Deployment:
    deployment_name: str
    repository_prefix: str
    repository_name: str
    namespace: str
    credential_name: str
    image_tag: str = 'latest'

    @property
    def kvs_key_image_pushed_at(self):
        return f'Deployment-{self.namespace}-{self.deployment_name}-image_pushed_at'


def regular_strftime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def process_deployment(
    *,
    deployment: Deployment,
    credentials_manager: CredentialsManager,
    kv_store: AbstractKVStore,
):
    """
    Process a single Deployment.
    """
    logger.info(f'[{deployment.deployment_name}] Processing deployment ...')
    # authorize
    credential = credentials_manager.get_credential(deployment.credential_name)

    if credential.is_credential_secret_update_required():
        credential.update_credential_secret()

    # describe image
    ecr_client = credential.get_ecr_client()
    response = ecr_client.describe_images(
        repositoryName=deployment.repository_name
    )
    # Filter by imageTag.
    if deployment.image_tag:
        _images = [
            image
            for image in response['imageDetails']
            if deployment.image_tag in image.get('imageTags', [])
        ]
    else:
        _images = response['imageDetails']

    if not _images:
        logger.warning(
            f'[{deployment.deployment_name}] '
            f'Image {deployment.repository_name} not found. '
            'Check ECR Repository page, and repositoryName in config.yaml, '
            f'imageTag ({deployment.image_tag}).'
        )
        return

    image = _images[0]
    image_pushed_at: datetime.datetime = image['imagePushedAt']

    # get last updated at
    last_pushed_at = kv_store.get(deployment.kvs_key_image_pushed_at)
    if last_pushed_at and last_pushed_at >= image_pushed_at:
        logger.info(
            f'[{deployment.deployment_name}] No update required. '
            f'{deployment.repository_name} '
            f'last_pushed_at={regular_strftime(last_pushed_at)}, '
            f'image_pushed_at={regular_strftime(image_pushed_at)}'
        )
        return

    logger.info(
        f'[{deployment.deployment_name}] Updating deployment: '
        f'last_pushed_at={regular_strftime(last_pushed_at)}, '
        f'image_pushed_at={regular_strftime(image_pushed_at)}'
    )

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
        },
    )
    logger.debug(
        f'[{deployment.deployment_name}] k8s patched response: {response}'
    )
    kv_store.set(
        deployment.kvs_key_image_pushed_at,
        image_pushed_at,
    )
    logger.info(f'[{deployment.deployment_name}] Updated deployment.')
