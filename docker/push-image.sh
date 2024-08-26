#!/usr/bin/env zsh

cd "$(dirname $0)" || exit

. ./config.sh

docker push ${image_name}:${image_tag}
docker push ${image_name}:latest
