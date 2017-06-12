#!/bin/bash

sudo mkdir -p /var/openbmp/mysql
sudo chmod 777 /var/openbmp/mysql

cp ../consumer.py ../docker/consumer/consumer.py
cp ../config.yaml ../docker/consumer/config.yaml

cd ../docker/consumer

docker build -t kakfa-slapi .
