FROM akshshar/confluent-python


RUN apt-get update && apt-get install -y git vim python-pip python-dev libsnappy-dev

RUN pip --proxy=$https_proxy install --upgrade pip

RUN pip --proxy=$https_proxy install redis py-radix pyyaml

RUN export https_proxy=$https_proxy && git clone https://github.com/OpenBMP/openbmp-python-api-message.git /openbmp

RUN pip install /openbmp

RUN rm -rf /openbmp
