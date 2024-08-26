#!/usr/bin/env zsh

cd "$(dirname $0)" || exit

. ./config.sh

cd ..

docker build --platform linux/amd64 \
  -t ${image_name}:${image_tag} \
  --build-arg APP_VERSION=${image_tag} \
  --build-arg BUILD_DATE="$(date '+%Y-%m-%d %H:%M')" \
  -f docker/Dockerfile .
docker tag ${image_name}:${image_tag} ${image_name}:latest
