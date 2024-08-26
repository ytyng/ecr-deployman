#!/usr/bin/env bash

image_name=ytyng/ecr-deployman
container_name=ecr-deployman

# GITHUB_RUN_NUMBER があれば使い、なければ git rev-list --count HEAD を使う
tag_suffix=${GITHUB_RUN_NUMBER:-$(git rev-list --count HEAD)}
image_tag=0.1.${tag_suffix}
