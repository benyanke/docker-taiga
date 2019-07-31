FROM python:3.5
MAINTAINER Ben Yanke <ben@benyanke.com>

ENV DEBIAN_FRONTEND noninteractive

RUN set -x && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-cairo \
        locales \
        gettext \
        ca-certificates \
        nginx \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8 && dpkg-reconfigure locales

WORKDIR /usr/src/taiga-back
COPY taiga-back/requirements.txt /usr/src/taiga-back/
RUN pip install --no-cache-dir -r requirements.txt

COPY taiga-back /usr/src/taiga-back
COPY taiga-front-dist/ /usr/src/taiga-front-dist
COPY docker-settings.py /usr/src/taiga-back/settings/docker.py
COPY conf/locale.gen /etc/locale.gen
COPY conf/nginx/nginx.conf /etc/nginx/nginx.conf
COPY conf/nginx/taiga.conf /etc/nginx/conf.d/default.conf
COPY conf/nginx/ssl.conf /etc/nginx/ssl.conf
COPY conf/nginx/taiga-events.conf /etc/nginx/taiga-events.conf

# Setup symbolic links for configuration files
RUN mkdir -p /taiga
COPY conf/taiga/local.py /taiga/local.py
# COPY conf/taiga/conf.json /taiga/conf.json
COPY conf/taiga/conf.json /taiga/conf-orig.json
RUN ln -s /taiga/local.py /usr/src/taiga-back/settings/local.py && \
    ln -s /taiga/conf.json /usr/src/taiga-front-dist/dist/conf.json

# Backwards compatibility
RUN mkdir -p /usr/src/taiga-front-dist/dist/js/ && ln -s /taiga/conf.json /usr/src/taiga-front-dist/dist/js/conf.json

# specify LANG to ensure python installs locals properly
# fixes benhutchins/docker-taiga-example#4
# ref benhutchins/docker-taiga#15
ENV LANG C

## Install Slack extension
RUN LC_ALL=C pip install --no-cache-dir taiga-contrib-slack && \
    mkdir -p /usr/src/taiga-front-dist/dist/plugins/slack/ && \
    SLACK_VERSION=$(pip show taiga-contrib-slack | awk '/^Version: /{print $2}') && \
    echo "taiga-contrib-slack version: $SLACK_VERSION" && \
    curl https://raw.githubusercontent.com/taigaio/taiga-contrib-slack/$SLACK_VERSION/front/dist/slack.js -o /usr/src/taiga-front-dist/dist/plugins/slack/slack.js && \
    curl https://raw.githubusercontent.com/taigaio/taiga-contrib-slack/$SLACK_VERSION/front/dist/slack.json -o /usr/src/taiga-front-dist/dist/plugins/slack/slack.json

## Install LDAP extension (only one will be used, selected in config too)
RUN pip install --no-cache-dir taiga-contrib-ldap-auth-ext

# Use this instead of the one above to use the fork (which may have features not yet released in the one above)
# RUN pip install --no-cache-dir git+git://github.com/benyanke/taiga-contrib-ldap-auth-ext.git

RUN echo "LANG=en_US.UTF-8" >> /etc/default/locale && \
    echo "LC_ALL=en_US.UTF-8" >> /etc/default/locale && \
    echo "LC_TYPE=en_US.UTF-8" >> /etc/default/locale && \
    echo "LC_MESSAGES=POSIX" >> /etc/default/locale && \
    echo "LANGUAGE=en" >> /etc/default/locale


ENV LANG en_US.UTF-8
ENV LC_TYPE en_US.UTF-8
ENV TAIGA_SSL False
ENV TAIGA_ENABLE_EMAIL False
ENV TAIGA_HOSTNAME localhost
ENV TAIGA_SECRET_KEY "!!!REPLACE-ME-j1598u1J^U*(y251u98u51u5981urf98u2o5uvoiiuzhlit3)!!!"

RUN locale-gen en_US.UTF-8 && locale -a

RUN python manage.py collectstatic --noinput

RUN locale -a

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80 443

VOLUME /usr/src/taiga-back/media

# Static file serving
HEALTHCHECK CMD curl --fail http://localhost:80/conf.json || exit 1

# DB Backend
# HEALTHCHECK CMD curl --fail http://localhost:80/api/v1/ || exit 1


COPY checkdb.py /checkdb.py
COPY docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "-w 3", "-t 60", "--pythonpath=.", "-b 127.0.0.1:8000", "taiga.wsgi"]
