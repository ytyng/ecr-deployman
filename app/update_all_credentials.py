#!/usr/bin/env python3

"""
ecr-deployman update_credential script
"""

import dotenv
from config_loader import load_config
from credentials import CredentialsManager
from deployments import Deployment
from kv_store import SimpleKVStore
from logger import logger


def main():
    dotenv.load_dotenv()
    config = load_config()
    kvs = SimpleKVStore()
    credentials_manager = CredentialsManager(
        config['awsEcrCredentials'], kv_store=kvs
    )
    deployments = [
        Deployment.from_config(deploy) for deploy in config['deployments']
    ]

    processed_credential_names = set()

    for deployment in deployments:
        if deployment.credential_name in processed_credential_names:
            continue
        logger.info(
            f'Updating credential: {deployment.deployment_name} /'
            f' {deployment.credential_name}'
        )
        credential = credentials_manager.get_credential(
            deployment.credential_name
        )

        credential.update_credential_secret()
        processed_credential_names.add(deployment.credential_name)
        logger.info('Updated.')

    logger.info('All credentials updated successfully.')


if __name__ == '__main__':
    main()
