#!/bin/bash

https_proxy=$1

cd /vagrant/compose/docker/controller
docker build -t controller --build-arg https_proxy=$https_proxy .

cd /vagrant/compose/docker/grpcio
docker build -t grpcio --build-arg https_proxy=$https_proxy . 
