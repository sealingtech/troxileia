FROM centos:centos7
MAINTAINER SealingTech

RUN yum -y update \
    #Install Python repo, Python 3.6  and addons
    && yum -y install https://centos7.iuscommunity.org/ius-release.rpm \
    && yum -y install python36u python36u-libs python36u-devel python36u-pip \
    && yum -y clean all \
    #Install Python Kubernetes client lib.
    && python3.6 -m pip install kubernetes paramiko
ENV PYTHONUNBUFFERED=0
#Put scripts inside container
COPY scripts ./
#When the container starts run the python controller
CMD ["python3.6", "main.py"]
