#!/bin/bash

# version 2022-08-26 15:20

git pull
chmod +x build.sh

docker image build -t revenberg/dockerprometeus2fluxdb:latest .

docker push revenberg/dockerprometeus2fluxdb:latest

# testing: 

echo "==========================================================="
echo "=                                                         ="
echo "= docker-compose up                                       ="
echo "=                                                         ="
echo "==========================================================="

docker-compose up
