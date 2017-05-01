FROM centos:6.6
MAINTAINER anton.zakharov@crim.ca

# Install required libraries -------------------
RUN rpm -ivh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

RUN yum install -y\
    hg \
    python2-devel \
    gcc \
    python-pip \
    wget \
    tar

# Missing in the base centos install -----------

RUN mkdir -p /tmp/install/netifaces/

RUN cd /tmp/install/netifaces &&\
    wget -O "netifaces-0.10.4.tar.gz" \
    "https://pypi.python.org/packages/source/n/netifaces/netifaces-0.10.4.tar.gz#md5=36da76e2cfadd24cc7510c2c0012eb1e"

RUN cd /tmp/install/netifaces/ &&\
    tar xvzf netifaces-0.10.4.tar.gz

RUN cd /tmp/install/netifaces/netifaces-0.10.4 &&\
    python setup.py install

RUN pip install gunicorn

ENV JASS_CONFIG_PATH "/opt/jass_deploy/config.ini"
ENV JASS_VERSION 1.0.2

RUN mkdir -p /opt/jass_deploy

COPY . /opt/jass_deploy
RUN cd /opt/jass_deploy && pip install -e .

RUN chmod +x /opt/jass_deploy/jass_startup.sh

EXPOSE 5000

WORKDIR /opt/jass_deploy
CMD ["./jass_startup.sh"]
