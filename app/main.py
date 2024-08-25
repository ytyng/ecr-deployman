#!/usr/bin/env python3
"""
ecr-deployman main loop
"""
from dataclasses import dataclass
from pathlib import Path

import yaml
import os

def config_dirs():
    curdir = Path(__file__).resolve().parent
    print(curdir)
    yield curdir
    yield curdir.parent

def load_config():
    # 親ディレクトリをすべて確認して、config.yaml があったらパースして返す
    for d in config_dirs():
        for config_path in [
            d / "config.yaml",
            d / "config.yml",
        ]:
            if config_path.exists():
                with config_path.open() as f:
                    return yaml.safe_load(f)
    raise FileNotFoundError('config.yaml not found')

@dataclass
class EcrCredential:
    name: str
    awsAccessKeyId: str
    awsSecretAccessKey: str
    namespace: str
    secretName: str

class CredentialsManager:
    """
    AWS の接続情報を管理するクラス
    """
    def __init__(self, credentials_settings):
        self.ecr_credentials = {
            cred['name']: EcrCredential(**cred)
            for cred in credentials_settings
        }


@dataclass
class Deployment:
    deploymentName: str
    repositoryPrefix: str
    repositoryName: str
    namespace: str
    credentialName: str


def process_deployment(*, deployment: Deployment, credentials_manager: CredentialsManager):
    """
    デプロイメントの処理
    """
    print(f"Processing deployment: {deployment.deploymentName}")


def main_loop():
    """
    Main loop
    """
    config = load_config()
    credentials_manager = CredentialsManager(config['awsEcrCredentials'])
    deployments = [
        Deployment(**deploy)
        for deploy in config['deployments']
    ]

    for deployment in deployments:
        process_deployment(
            deployment=deployment,
            credentials_manager=credentials_manager
        )
        break




if __name__ == "__main__":
    main_loop()
