FROM golang:stretch as confd

ARG CONFD_VERSION=0.16.0

ADD https://github.com/kelseyhightower/confd/archive/v${CONFD_VERSION}.tar.gz /tmp/

RUN set -x \
    && mkdir -p /go/src/github.com/kelseyhightower/confd \
    && cd /go/src/github.com/kelseyhightower/confd \
    && tar --strip-components=1 -zxf /tmp/v${CONFD_VERSION}.tar.gz \
    && go install github.com/kelseyhightower/confd \
    && rm -rf /tmp/v${CONFD_VERSION}.tar.gz \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# FROM debian:jessie as target

# At last try, the legacy software won't install on debian:stretch.

# # ###
# # Java install,
# #   copied from https://github.com/docker-library/openjdk/blob/93316d3b14379d29fe0cd363bd6839eb8dd8cc7b/7-jre/Dockerfile
# # ###

# # A few problems with compiling Java from source:
# #  1. Oracle.  Licensing prevents us from redistributing the official JDK.
# #  2. Compiling OpenJDK also requires the JDK to be installed, and it gets
# #       really hairy.

# RUN apt-get update && apt-get install -y --no-install-recommends \
# 		bzip2 \
# 		unzip \
# 		xz-utils \
# 	&& rm -rf /var/lib/apt/lists/*

# # Default to UTF-8 file.encoding
# ENV LANG C.UTF-8

# # add a simple script that can auto-detect the appropriate JAVA_HOME value
# # based on whether the JDK or only the JRE is installed
# RUN { \
# 		echo '#!/bin/sh'; \
# 		echo 'set -e'; \
# 		echo; \
# 		echo 'dirname "$(dirname "$(readlink -f "$(which javac || which java)")")"'; \
# 	} > /usr/local/bin/docker-java-home \
# 	&& chmod +x /usr/local/bin/docker-java-home

# # do some fancy footwork to create a JAVA_HOME that's cross-architecture-safe
# RUN ln -svT "/usr/lib/jvm/java-7-openjdk-$(dpkg --print-architecture)" /docker-java-home
# ENV JAVA_HOME /docker-java-home/jre

# RUN set -ex; \
# 	\
# 	apt-get update; \
# 	apt-get install -y openjdk-7-jre-headless; \
# 	rm -rf /var/lib/apt/lists/*; \
# 	\
# # verify that "docker-java-home" returns what we expect
# 	[ "$(readlink -f "$JAVA_HOME")" = "$(docker-java-home)" ]; \
# 	\
# # update-alternatives so that future installs of other OpenJDK versions don't change /usr/bin/java
# 	update-alternatives --get-selections | awk -v home="$(readlink -f "$JAVA_HOME")" 'index($3, home) == 1 { $2 = "manual"; print | "update-alternatives --set-selections" }'; \
# # ... and verify that it actually worked for one of the alternatives we care about
# 	update-alternatives --query java | grep -q 'Status: manual'

# A few reasons for installing distribution-provided OpenJDK:
#
#  1. Oracle.  Licensing prevents us from redistributing the official JDK.
#
#  2. Compiling OpenJDK also requires the JDK to be installed, and it gets
#     really hairy.
#
#     For some sample build times, see Debian's buildd logs:
#       https://buildd.debian.org/status/logs.php?pkg=openjdk-8


# # ###
# # / End copy for Java Install
# # ###

# Start with the java base, since it is the hardest to install
FROM openjdk:7-jre-jessie as python24

# ###
# Install System Dependencies
# ###

RUN set -x \
    && mkdir -p /usr/share/man/man1 \
    && mkdir -p /usr/share/man/man7 \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
      ca-certificates \
      git \
      build-essential \
      wget \
      postgresql-client \
      libpq-dev \
      libjpeg-dev \
      libpng-dev \
      dpkg-dev \
      zlib1g-dev \
      libreadline6-dev \
      libncurses5-dev \
      libssl-dev \
      libxml2-dev \
      libxslt-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ###
# Install Python 2.4
# ###

COPY downloads/* /tmp/
WORKDIR /tmp/

RUN set -x \
    && tar xzf /tmp/Python-2.4.6.tgz \
    && cd Python-2.4.6 \
    && sed -i -E 's%^(\s*lib_dirs = .*)$%\1 "/usr/lib/x86_64-linux-gnu",%g' setup.py \
    && ./configure  \
    && make \
    && make install \
    && cd .. \
    && rm -rf /tmp/Python-2.4.6.tgz

RUN set -x \
    && tar xzf /tmp/setuptools-1.4.2.tar.gz \
    && cd setuptools-1.4.2 \
    && python2.4 setup.py install \
    && cd .. \
    && rm -rf /tmp/ez_setup.py setuptools*


RUN set -x \
    && tar xzf /tmp/pip-1.1.tar.gz \
    && cd pip-1.1 \
    && python2.4 setup.py install \
    && cd .. \
    && rm -rf /tmp/pip-1.1.tar.gz

# TODO: clean up /tmp

# ###
# /END Install Python2.4
# ###

# ############################################################################
# FOUNDATION
# ############################################################################

FROM python24 as foundation

COPY --from=confd /go/bin/confd /usr/local/bin/confd
RUN mkdir -p /etc/confd/conf.d/

RUN set -x \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
      unoconv \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN set -x \
    && mkdir -p /app/downloads /app/products /app/var \
    && chown www-data:www-data /app

# ###
# Use a virtualenv
# ###

COPY downloads/virtualenv-1.7.2.tar.gz /tmp
RUN set -x \
    && cd /tmp \
    && tar xzf /tmp/virtualenv-1.7.2.tar.gz

USER www-data
RUN python2.4 /tmp/virtualenv-1.7.2/virtualenv.py /app

# ###
# Pull in the application files
# ###

USER root
RUN rm -rf /tmp/*
COPY ["bootstrap.py", "rhaptos-versions.cfg", "docker-base.cfg", "docker-buildout.cfg", "libs.cfg", "/app/"]
COPY scripts /app/scripts
COPY ["downloads/Python-2.4.6.tgz", "downloads/jing-20081028.zip", "downloads/pip-1.1.tar.gz", "downloads/setuptools-1.4.2.tar.gz", "/app/downloads/"]
WORKDIR /app
ADD https://raw.githubusercontent.com/Connexions/cnx-deploy/master/environments/__prod_envs/files/versions.cfg /app/docker-versions.cfg
RUN set -x \
    && chown -R www-data:www-data .

# ###
# Continue setting up the application as the runtime user
# ###

USER www-data

RUN set -x \
    && . bin/activate \
    && bin/pip install --index-url=https://pypi.python.org/simple/ \
      readline \
      simplejson==1.9.2

RUN set -x \
    && . bin/activate \
    && bin/pip install --index-url=https://pypi.python.org/simple/ \
      lxml==3.2.1 \
      python-memcached==1.48 \
      hashlib==20081119

# ###
# Build the application
# ###

RUN set -x \
    && . bin/activate \
    && bin/python2.4 bootstrap.py \
    && bin/buildout -c docker-buildout.cfg -vvvv
# FIXME: buildout doesn't return a non-zero exit code... we must check the install

COPY .dockerfiles/docker-entrypoint.sh /usr/local/bin/
COPY .dockerfiles/etc/confd /etc/confd

ENV LEGACY_ZEO_HOST=127.0.0.1

ENTRYPOINT ["docker-entrypoint.sh"]


# ############################################################################
# ZEO
# ############################################################################

FROM foundation as zeo
# Nothing more to do...


# ############################################################################
# WEB
# ############################################################################

FROM foundation as web
# TODO: install remaining web client dependencies


# ############################################################################
# PDF-GEN
# ############################################################################

FROM foundation as pdf-gen

# TODO: install all the pdf-gen dependencies
# TODO: install PrinceXML
