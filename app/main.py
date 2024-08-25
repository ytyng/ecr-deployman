#!/usr/bin/env python3
"""
ecr-deployman main loop
"""
import time

from config_loader import load_config
from credentials import CredentialsManager
from deployments import Deployment, process_deployment
from kv_store import SimpleKVStore
from logger import logger


def main_loop():
    """
    Main loop
    """
    logger.debug('Preparing to start application.')

    config = load_config()
    kvs = SimpleKVStore()
    credentials_manager = CredentialsManager(
        config['awsEcrCredentials'], kv_store=kvs
    )
    deployments = [
        Deployment.from_config(deploy) for deploy in config['deployments']
    ]

    logger.info(
        'Application started. '
        f'{len(credentials_manager.ecr_credentials)} credentials found. '
        f'{len(deployments)} deployments found.'
    )

    while True:
        for deployment in deployments:
            try:
                process_deployment(
                    deployment=deployment,
                    credentials_manager=credentials_manager,
                    kv_store=kvs,
                )
            except Exception as e:
                logger.warning(
                    f'[ERROR] {deployment.deployment_name}: '
                    f'{e.__class__.__name__}:{e}'
                )

        time.sleep(60)


if __name__ == "__main__":
    main_loop()
