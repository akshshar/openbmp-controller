#!/bin/bash

# http_proxy and https_proxy variables are passed in through the Vagrantfile 
# which in turn gets it from the user's environment when executing vagrant up.

set -x

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

cat > http_proxy << EOF
[Service]
Environment="HTTP_PROXY=$http_proxy"
EOF

cat > https_proxy << EOF
[Service]
Environment="HTTP_PROXY=$https_proxy"
EOF

cp /vagrant/http-proxy.conf /etc/systemd/system/docker.service.d/
cp /vagrant/https-proxy.conf /etc/systemd/system/docker.service.d/
cp /vagrant/daemon.json /etc/docker/daemon.json

systemctl daemon-reload
systemctl restart docker

pip --proxy=$https_proxy install --upgrade pip
pip --proxy=$https_proxy install docker-compose
 
docker pull ubuntu:16.04
docker pull  akshshar/confluent-python

cp -r ../../compose ./compose
cp ../../lib ./

git clone https://github.com/akshshar/route-shuttle

sudo mkdir -p /var/openbmp/mysql
sudo chmod 777 /var/openbmp/mysql

docker-compose up -d
