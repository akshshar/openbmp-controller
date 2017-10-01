#!/bin/bash

sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce
sudo usermod -aG docker vagrant

docker run -itd --net=host -p 2181:2181 -p 9092:9092 --env ADVERTISED_HOST='10.1.3.10' --env ADVERTISED_PORT=9092 --name=kafka spotify/kafka
