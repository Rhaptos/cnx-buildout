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

WORKDIR /tmp/

RUN set -x \
    && wget https://www.python.org/ftp/python/2.4.6/Python-2.4.6.tgz \
    && tar xzf /tmp/Python-2.4.6.tgz \
    && cd Python-2.4.6 \
    && sed -i -E 's%^(\s*lib_dirs = .*)$%\1 "/usr/lib/x86_64-linux-gnu",%g' setup.py \
    && ./configure  \
    && make \
    && make install \
    && cd .. \
    && rm -rf /tmp/*

RUN set -x \
    && wget https://files.pythonhosted.org/packages/61/3c/8d680267eda244ad6391fb8b211bd39d8b527f3b66207976ef9f2f106230/setuptools-1.4.2.tar.gz \
    && tar xzf /tmp/setuptools-1.4.2.tar.gz \
    && cd setuptools-1.4.2 \
    && python2.4 setup.py install \
    && cd .. \
    && rm -rf /tmp/*

RUN set -x \
    && wget https://files.pythonhosted.org/packages/25/57/0d42cf5307d79913a082c5c4397d46f3793bc35e1138a694136d6e31be99/pip-1.1.tar.gz \
    && tar xzf /tmp/pip-1.1.tar.gz \
    && cd pip-1.1 \
    && python2.4 setup.py install \
    && cd .. \
    && rm -rf /tmp/*

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

# Install CNXML DTD files
RUN set -x \
    && apt-get update \
    && apt-get install --no-install-recommends -y apt-transport-https \
    && echo "deb [ trusted=yes ] https://packages.cnx.org/ deb/" > /etc/apt/sources.list.d/packages.cnx.org.list \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
      connexions-cnxml-0.8 \
      connexions-cnxml-0.7 \
      connexions-mdml-0.5 \
      connexions-memcases-xml \
      connexions-qml-1.0 \
      connexions-bibtexml-1.0 \
      connexions-mathml-2.0 \
      connexions-mathml-3.0 \
      connexions-collxml-1.0 \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ###
# Use a virtualenv
# ###

USER www-data
RUN set -x \
    && cd /tmp \
    && wget https://files.pythonhosted.org/packages/16/86/7b88d35d0a353ec70e42aa37fd8b0bd1c643419c80f022ffaafa4d6449f0/virtualenv-1.7.2.tar.gz \
    && tar xzf /tmp/virtualenv-1.7.2.tar.gz \
    && python2.4 /tmp/virtualenv-1.7.2/virtualenv.py /app \
    && rm -rf /tmp/*

# ###
# Pull in the application files
# ###

USER root
WORKDIR /app

RUN set -x \
    && wget -O /app/downloads/jing-20081028.zip https://raw.githubusercontent.com/openstax/cnx-deploy/28bc2804652f2939f53c2a2c533c362d3bc9fbc0/files/src/cnx-buildout/downloads/jing-20081028.zip
ADD https://raw.githubusercontent.com/Connexions/cnx-deploy/master/environments/__prod_envs/files/versions.cfg /app/docker-versions.cfg
COPY ["bootstrap.py", "rhaptos-versions.cfg", "docker-base.cfg", "docker-buildout.cfg", "libs.cfg", "/app/"]
COPY scripts /app/scripts
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
    && bin/python2.4 bootstrap.py -c docker-buildout.cfg \
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
EXPOSE 8100


# ############################################################################
# WEB
# ############################################################################

FROM foundation as web
# TODO: install remaining web client dependencies
EXPOSE 8080

# ############################################################################
# PDF-GEN
# ############################################################################

FROM foundation as pdf-gen
USER root
# Install all the pdf-gen dependencies
RUN set -x \
    && mkdir -p /usr/share/man/man1 \
    && mkdir -p /usr/share/man/man7 \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
      python-imaging \
      gif2png \
      cjk-latex \
      texlive-latex-extra \
      xsltproc \
      xvfb \
      xfonts-base \
      libreoffice \
      imagemagick \
      tralics \
      unzip \
      libxml2-utils \
      texlive-latex3 \
      libedit-dev \
      zip \
      libreoffice-script-provider-python \
      ruby \
      inkscape \
      docbook-xsl-ns \
      texlive-fonts-recommended \
      memcached \
      librsvg2-bin \
      otf-stix \
      # openjdk-8-jdk \
      jpegoptim \
      fontconfig \
      fontconfig-config \
      fonts-cabin \
      fonts-comfortaa \
      fonts-crosextra-caladea \
      fonts-crosextra-carlito \
      fonts-dejavu \
      fonts-dejavu-core \
      fonts-dejavu-extra \
      fonts-ebgaramond \
      fonts-ebgaramond-extra \
      fonts-font-awesome \
      fonts-freefont-otf \
      fonts-freefont-ttf \
      fonts-gfs-artemisia \
      fonts-gfs-complutum \
      fonts-gfs-didot \
      fonts-gfs-neohellenic \
      fonts-gfs-olga \
      fonts-gfs-solomos \
      fonts-inconsolata \
      fonts-junicode \
      fonts-lato \
      fonts-liberation \
      fonts-linuxlibertine \
      fonts-lmodern \
      fonts-lobster \
      fonts-lobstertwo \
      fonts-oflb-asana-math \
      fonts-opensymbol \
      # fonts-roboto-hinted \
      fonts-sil-gentium \
      fonts-sil-gentium-basic \
      fonts-sil-gentiumplus \
      fonts-stix \
      fonts-texgyre \
      gsfonts \
      libfont-afm-perl \
      libfontconfig1:amd64 \
      libfontenc1:amd64 \
      libxfont1:amd64 \
      texlive-font-utils \
      texlive-fonts-extra \
      texlive-fonts-extra-doc \
      texlive-fonts-recommended \
      texlive-fonts-recommended-doc \
      xfonts-base \
      xfonts-encodings \
      xfonts-utils \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
# Install PrinceXML
ENV PRINCE_XML_DEB=prince_12.4-1_debian8.10_amd64.deb
RUN set -x \
    && wget -P /tmp/ https://www.princexml.com/download/${PRINCE_XML_DEB} \
    && dpkg -i /tmp/${PRINCE_XML_DEB} \
    && rm -rf /tmp/*

USER www-data
EXPOSE 8080

# TODO: Allow for PrinceXML license to be added at runtime
# TODO: Install URW fonts
# TODO: Install addtional fonts
