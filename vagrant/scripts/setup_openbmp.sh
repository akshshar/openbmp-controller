#!/bin/bash

# http_proxy and https_proxy variables are passed in through the Vagrantfile 
# which in turn gets it from the user's environment when executing vagrant up.

set -x

# Install docker-ce and python-pip

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

adduser vagrant docker


# Set up http/https proxy for the docker daemon

if [[ $http_proxy ]]; then

   mkdir /etc/systemd/system/docker.service.d/
cat > http-proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=$http_proxy"
EOF

fi

if [[ $https_proxy ]]; then

cat > https-proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=$https_proxy"
EOF

fi

if [[ $insecure_registry ]]; then
cat > daemon.json << EOF
{
  "insecure-registries": ["$insecure_registry"]
}
EOF
fi

cp /home/vagrant/http-proxy.conf /etc/systemd/system/docker.service.d/
cp /home/vagrant/https-proxy.conf /etc/systemd/system/docker.service.d/
cp /home/vagrant/daemon.json /etc/docker/daemon.json

systemctl daemon-reload
systemctl restart docker


# Install docker-compose
pip --proxy=$https_proxy install --upgrade pip
pip --proxy=$https_proxy install docker-compose


# Clone route-shuttle with the openbmp-client and plugin code
git clone https://github.com/akshshar/route-shuttle /home/vagrant/route-shuttle

# Copy over the generated python bindings (added by user to vagrant folder) to the route-shuttle folder
cp -r /vagrant/lindt-objmodel/grpc/python/src/genpy/* /home/vagrant/route-shuttle/genpy

# Build docker images
/vagrant/compose/docker/build_all.sh $https_proxy

# Spin up the docker topology

sudo mkdir -p /var/openbmp/mysql
sudo chmod 777 /var/openbmp/mysql

cd /vagrant/compose
docker-compose up -d
