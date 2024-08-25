import base64
import datetime
import json
from dataclasses import dataclass

import boto3
from kubernetes import client, config

from kv_store import AbstractKVStore


@dataclass
class EcrCredential:
    name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
    namespace: str
    secret_name: str
    kv_store: AbstractKVStore
    # kube_config_file, kube_config_context は指定してあれば使う。
    # ローカルで開発する際は使う。Kubernetes Pod で動かす場合は指定しない。
    kube_config_file: str | None = None
    kube_config_context: str | None = None

    def get_ecr_client(self):
        # cached_property にすると少し速そうだが
        # 安定性を重視して毎回コンストラクトする。
        return boto3.client(
            'ecr',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

    def get_k8s_client(self) -> client.ApiClient:
        # cached_property にすると少し速そうだが
        # 安定性を重視して毎回コンストラクトする。
        return config.new_client_from_config(
            config_file=self.kube_config_file,
            context=self.kube_config_context,
        )

    @property
    def kvs_key_secret_updated_at(self):
        return f'EcrCredential-{self.name}-secret_updated_at'

    def is_credential_secret_update_required(self):
        """
        Secret の更新が必要かどうかを判定する。
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
        # get secret
        ecr_client = self.get_ecr_client()
        response = ecr_client.get_authorization_token()
        auth_data = response['authorizationData'][0]
        auth_token = base64.b64decode(
            auth_data['authorizationToken']).decode('utf-8')
        username, password = auth_token.split(':')
        # DockerリポジトリのURL
        proxy_endpoint = auth_data['proxyEndpoint'].replace('https://', '')

        # Secret の作成
        secret_data = {
            'auths': {
                proxy_endpoint: {
                    'username': username,
                    'password': password,
                    'auth': auth_data['authorizationToken']
                }
            }
        }
        secret = client.V1Secret(
            api_version='v1',
            kind='Secret',
            type='kubernetes.io/dockerconfigjson',
            metadata=client.V1ObjectMeta(
                name=self.secret_name,
                namespace=self.namespace
            ),
            data={
                '.dockerconfigjson': base64.b64encode(
                    json.dumps(secret_data, ensure_ascii=False).encode()
                ).decode()
            },
        )

        k8s_client = self.get_k8s_client()
        v1 = client.CoreV1Api(k8s_client)
        v1.delete_namespaced_secret(
            name=self.secret_name,
            namespace=self.namespace,
            body=client.V1DeleteOptions(),
        )
        v1.create_namespaced_secret(
            namespace=self.namespace,
            body=secret,
        )
        self.kv_store.set(
            self.kvs_key_secret_updated_at,
            datetime.datetime.now(),
        )


class CredentialsManager:
    """
    AWS の接続情報を管理するクラス
    """

    def __init__(self, credentials_settings, *, kv_store: AbstractKVStore):
        self.ecr_credentials = {
            cred['name']: EcrCredential(
                name=cred['name'],
                aws_access_key_id=cred['awsAccessKeyId'],
                aws_secret_access_key=cred['awsSecretAccessKey'],
                region_name=cred['regionName'],
                namespace=cred['namespace'],
                secret_name=cred['secretName'],
                kv_store=kv_store,
                kube_config_file=cred.get('kubeConfigFile'),
                kube_config_context=cred.get('kubeConfigContext'),
            ) for cred in credentials_settings
        }

    def get_credential(self, credential_name: str) -> EcrCredential:
        return self.ecr_credentials[credential_name]
