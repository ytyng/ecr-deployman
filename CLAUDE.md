# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

ecr-deployman is a tool that monitors image repositories in ECR (Amazon Elastic Container Registry) and deploys to Kubernetes when a new image is pushed.

Main features:
- Monitoring ECR repositories (every minute)
- Automatic update of the Kubernetes Deployment when a new image is detected
- Slack notifications
- Support for multiple ECR credential and deployment settings

## Project Structure

```
app/
├── main.py              # Entry point, main loop
├── config_loader.py     # Loads the YAML config file
├── credentials.py       # AWS ECR credential management
├── deployments.py       # Deployment processing, ECR monitoring, K8s updates
├── kv_store.py         # Simple key-value storage
├── logger.py           # Logging configuration
├── message_utils.py    # Builds Slack notification messages
└── storage/            # Directory for persisted data

docker/
├── Dockerfile          # Container image build definition
├── build.sh           # Build script
├── config.sh          # Docker settings (image name, etc.)
├── login.sh           # ECR login
├── push-image.sh      # Push to ECR
└── run.sh             # Local run

kubernetes/
└── pod.sample.yaml    # Sample Pod definition
```

## Development Commands

### Installing dependencies
```bash
pipenv install
```

### Running locally
```bash
pipenv run python app/main.py
```

### Building the Docker image
```bash
cd docker
./build.sh
```

### Pushing to ECR
```bash
cd docker
./login.sh
./push-image.sh
```

### Running Docker locally
```bash
cd docker
./run.sh
```

## Architecture Notes

### Monitoring flow
1. `main.py` processes each deployment every 60 seconds
2. `process_deployment()` in `deployments.py` checks for ECR image updates
3. If there is an update, it updates the K8s Deployment annotation to trigger a Pod restart
4. Sends a Slack notification

### State management
- `SimpleKVStore` persists the image push date/time and the Secret update date/time
- Stored as files in the `storage/` directory

### Kubernetes integration
- Automatically creates and updates the ECR credentials as a K8s Secret
- Updates the Deployment's `imageUpdatedAt` annotation to restart Pods

### Error handling
- Each deployment is processed independently; if one fails, the others continue
- Errors are logged and retried in the next cycle

## Configuration

Configuration is managed in `config.yaml`:
- `awsEcrCredentials`: AWS credential settings for accessing ECR
- `deployments`: Settings for the ECR repositories to monitor and their corresponding K8s Deployments

AWS credentials can be read from environment variables or written directly in the config.

## Testing Approach

Test scripts are placed in the `~scratch/` directory:
- `test_kubernetes.py`: Kubernetes connection test
- `test_webhook.py`: Slack webhook test
