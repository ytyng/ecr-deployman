import base64
import json
from dataclasses import dataclass

import boto3
from kubernetes import client, config


@dataclass
class EcrCredential:
    name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
    namespace: str
    secret_name: str
    # kube_config_file, kube_config_context は指定してあれば使う。
    # ローカルで開発する際は使う。Kubernetes Pod で動かす場合は指定しない。
    kube_config_file: str | None = None
    kube_config_context: str | None = None

    def get_ecr_client(self):
        return boto3.client(
            'ecr',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

    def get_k8s_configuration(self):
        client.Configuration()

    def get_k8s_client(self) -> client.ApiClient:

        # if self.kube_config_file or self.kube_config_context:
        #     # Kubernetes の設定ファイルを読み込む
        #     config.load_kube_config(config_file=self.kube_config_file, context=self.kube_config_context)
        #
        # # Kubernetes のクライアントを作成
        # return client.CoreV1Api()
        return config.new_client_from_config(
            config_file=self.kube_config_file,
            context=self.kube_config_context,
        )


    def update_credential_secret(self):
        # get secret
        ecr_client = self.get_ecr_client()
        response = ecr_client.get_authorization_token()
        auth_data = response['authorizationData'][0]
        auth_token = base64.b64decode(auth_data['authorizationToken']).decode('utf-8')
        username, password = auth_token.split(':')
        # DockerリポジトリのURL
        proxy_endpoint = auth_data['proxyEndpoint'].replace('https://', '')

        # Secret の作成
        secret_data = {
            'auths': {
                proxy_endpoint: {
                    'username': username,
                    'password': password,
                    # 'auth': base64.b64encode(
                    #     f"{username}:{password}".encode()
                    # ).decode()
                    'auth': auth_data['authorizationToken']
                }
            }
        }
        secret = client.V1Secret(
            api_version='v1',
            kind='Secret',
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


class CredentialsManager:
    """
    AWS の接続情報を管理するクラス
    """

    def __init__(self, credentials_settings):
        self.ecr_credentials = {
            cred['name']: EcrCredential(
                name=cred['name'],
                aws_access_key_id=cred['awsAccessKeyId'],
                aws_secret_access_key=cred['awsSecretAccessKey'],
                region_name=cred['regionName'],
                namespace=cred['namespace'],
                secret_name=cred['secretName'],
                kube_config_file=cred.get('kubeConfigFile'),
                kube_config_context=cred.get('kubeConfigContext'),
            ) for cred in credentials_settings
        }

    def get_credential(self, credential_name: str) -> EcrCredential:
        return self.ecr_credentials[credential_name]
