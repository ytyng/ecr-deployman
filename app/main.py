#!/usr/bin/env python3
"""
ecr-deployman main loop
"""
from config_loader import load_config
from credentials import CredentialsManager
from deployments import Deployment, process_deployment
from kv_store import SimpleKVStore

def main_loop():
    """
    Main loop
    """
    config = load_config()
    kvs = SimpleKVStore()
    credentials_manager = CredentialsManager(
        config['awsEcrCredentials'],
        kv_store=kvs
    )
    deployments = [
        Deployment(
            deployment_name=deploy['deploymentName'],
            repository_prefix=deploy['repositoryPrefix'],
            repository_name=deploy['repositoryName'],
            image_tag=deploy.get('imageTag'),
            namespace=deploy['namespace'],
            credential_name=deploy['credentialName'],
        )
        for deploy in config['deployments']
    ]

    for deployment in deployments:
        process_deployment(
            deployment=deployment,
            credentials_manager=credentials_manager,
            kv_store=kvs,
        )
        break


if __name__ == "__main__":
    main_loop()
