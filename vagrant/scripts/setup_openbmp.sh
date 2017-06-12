#!/bin/bash

set -x

http_proxy="http://proxy-wsa.esl.cisco.com:80"
https_proxy="http://proxy-wsa.esl.cisco.com:80"

export http_proxy=$http_proxy && export https_proxy=$https_proxy && sudo -E apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

export http_proxy=$http_proxy && export https_proxy=$https_proxy && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

export http_proxy=$http_proxy && export https_proxy=$https_proxy && sudo -E add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

export http_proxy=$http_proxy && export https_proxy=$https_proxy && sudo -E apt-get update

export http_proxy=$http_proxy && export https_proxy=$https_proxy && sudo -E apt-get install -y docker-ce python-pip  git

mkdir /etc/systemd/system/docker.service.d/
cp /vagrant/http-proxy.conf /etc/systemd/system/docker.service.d/
cp /vagrant/https-proxy.conf /etc/systemd/system/docker.service.d/
cp /vagrant/daemon.json /etc/docker/daemon.json

systemctl daemon-reload
systemctl restart docker

pip --proxy=$https_proxy install --upgrade pip
pip --proxy=$https_proxy install docker-compose
 
docker pull ubuntu:16.04
docker pull  akshshar/confluent-python

git clone http://gitlab.cisco.com/akshshar/openbmp-slapi.git /home/vagrant/openbmp-slapi
cd /home/vagrant/openbmp-slapi/compose
docker-compose up -d
