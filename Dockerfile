# Open BMP controller for NANOG hackathon

FROM ubuntu:trusty

RUN apt-get update
RUN apt-get install python-pip python-dev libsnappy-dev -y
RUN pip install --upgrade pip
RUN pip install grpcio py-radix
RUN pip install ydk-models-cisco-ios-xr

## Dependencies for openbmp messages
RUN pip install python-snappy kafka-python pyyaml

ADD . /tmp/



