#Start with Centos for the package source
FROM centos:centos7
#Who maintains the image (could be your email)
MAINTAINER Stech Training
#Best practice to always update
RUN yum -y update
RUN yum -y install yum-utils
#Install Python repo, Python 3.6  and some addons
RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm
RUN yum -y install python36u
RUN yum -y install python36u-libs
RUN yum -y install python36u-devel
RUN yum -y install python36u-pip
#Install Python Kubernetes client lib.

RUN python3.6 -m pip install kubernetes
RUN python3.6 -m pip install paramiko
RUN yum clean all -y
ENV PYTHONUNBUFFERED=0
#Put script inside container
COPY sensor_controller.py sensor_controller.py
COPY pod_controller.py pod_controller.py
COPY gigamon.py gigamon.py
COPY main.py main.py
#When the container starts run the python controller
CMD ["python3.6", "main.py"]