import base64
import datetime
import json
import os
from dataclasses import dataclass

import boto3
from kv_store import AbstractKVStore
from logger import logger

from kubernetes import client, config


def get_credential_value(var):
    """
    If credential variable is `fromEnv: ENV_VAR_NAME`,
    return the value of the environment variable.
    """
    if isinstance(var, dict):
        if env_key := var.get('fromEnv'):
            return os.environ.get(env_key)
    return var


@dataclass
class EcrCredential:
    name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
    namespace: str
    secret_name: str
    kv_store: AbstractKVStore
    # kube_config_file and kube_config_context are used if specified.
    # Use them when developing locally. Do not specify them
    # when running in a Kubernetes Pod.
    kube_config_file: str | None = None
    kube_config_context: str | None = None

    @classmethod
    def from_config(cls, config: dict, *, kv_store: AbstractKVStore):
        return cls(
            name=config['name'],
            aws_access_key_id=get_credential_value(config['awsAccessKeyId']),
            aws_secret_access_key=get_credential_value(
                config['awsSecretAccessKey']
            ),
            region_name=get_credential_value(config['regionName']),
            namespace=get_credential_value(config['namespace']),
            secret_name=get_credential_value(config['secretName']),
            kv_store=kv_store,
            kube_config_file=config.get('kubeConfigFile'),
            kube_config_context=config.get('kubeConfigContext'),
        )

    def get_ecr_client(self):
        # Using cached_property seems a bit faster,
        # but I prioritize stability and construct it every time.
        return boto3.client(
            'ecr',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        )

    def get_k8s_client(self) -> client.ApiClient:
        # Using cached_property seems a bit faster,
        # but I prioritize stability and construct it every time.
        if self.kube_config_file or self.kube_config_context:
            return config.new_client_from_config(
                config_file=self.kube_config_file,
                context=self.kube_config_context,
            )
        else:
            config.load_incluster_config()
            return client.ApiClient()

    @property
    def kvs_key_secret_updated_at(self):
        return f'EcrCredential-{self.name}-secret_updated_at'

    def is_credential_secret_update_required(self):
        """
        Determine if a secret needs to be updated.
        """
        secret_last_updated_at = self.kv_store.get(
            self.kvs_key_secret_updated_at,
        )
        if not secret_last_updated_at:
            return True
        return (
            datetime.datetime.now() - secret_last_updated_at
        ).total_seconds() > 3600

    def update_credential_secret(self):
        logger.info(f'Updating ECR credential secret: {self.name} ...')
        # get secret
        ecr_client = self.get_ecr_client()
        response = ecr_client.get_authorization_token()
        auth_data = response['authorizationData'][0]
        auth_token = base64.b64decode(auth_data['authorizationToken']).decode(
            'utf-8'
        )
        username, password = auth_token.split(':')
        # Docker repository URL
        proxy_endpoint = auth_data['proxyEndpoint'].replace('https://', '')

        # Create a Secret
        secret_data = {
            'auths': {
                proxy_endpoint: {
                    'username': username,
                    'password': password,
                    'auth': auth_data['authorizationToken'],
                }
            }
        }
        secret = client.V1Secret(
            api_version='v1',
            kind='Secret',
            type='kubernetes.io/dockerconfigjson',
            metadata=client.V1ObjectMeta(
                name=self.secret_name, namespace=self.namespace
            ),
            data={
                '.dockerconfigjson': base64.b64encode(
                    json.dumps(secret_data, ensure_ascii=False).encode()
                ).decode()
            },
        )

        k8s_client = self.get_k8s_client()
        v1 = client.CoreV1Api(k8s_client)
        try:
            v1.delete_namespaced_secret(
                name=self.secret_name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(),
            )
        except client.exceptions.ApiException as e:
            if e.status != 404:
                raise
            logger.info(f'404: {e.__class__.__name__}: {e}')
        v1.create_namespaced_secret(
            namespace=self.namespace,
            body=secret,
        )
        self.kv_store.set(
            self.kvs_key_secret_updated_at,
            datetime.datetime.now(),
        )
        logger.info(f'Updated ECR credential secret: {self.name}')


class CredentialsManager:
    """
    Class to manage AWS connection information
    """

    def __init__(self, credentials_settings, *, kv_store: AbstractKVStore):
        self.ecr_credentials = {
            cred['name']: EcrCredential.from_config(cred, kv_store=kv_store)
            for cred in credentials_settings
        }

    def get_credential(self, credential_name: str) -> EcrCredential:
        return self.ecr_credentials[credential_name]
