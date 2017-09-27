FROM akshshar/confluent-python


RUN apt-get update && apt-get install -y vim python-pip

RUN pip --proxy=$http_proxy install --upgrade pip

RUN pip --proxy=$http_proxy install pyyaml py2-ipaddress grpcio==0.13.1 redis

