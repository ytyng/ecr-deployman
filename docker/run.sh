#!/usr/bin/env bash

cd "$(dirname $0)" || exit

. ./config.sh

[ $(docker container ls -a -q -f name=${container_name}) ] && docker rm ${container_name}

docker run \
    --platform linux/amd64 \
    --rm -it \
    --name=${container_name} ${image_name}:${image_tag} "$@"
