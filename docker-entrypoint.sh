#!/bin/bash

# Setup database automatically if needed
if [ -z "$TAIGA_SKIP_DB_CHECK" ]; then
  echo "Running database check"
  python -u /checkdb.py
  DB_CHECK_STATUS=$?

  # If database did not come online, exit the container with error
  if [ $DB_CHECK_STATUS -eq 2 ]; then
    exit 1
  fi

  # Database migration check should be done in all startup in case of backend upgrade
  echo "Check for database migration"
  python manage.py migrate --noinput

  # Run the initial data seeder functions if we're starting with a fresh database
  if [ $DB_CHECK_STATUS -eq 1 ]; then
    echo "Configuring initial database"
    # python manage.py loaddata initial_user
    python manage.py loaddata initial_project_templates
    # python manage.py loaddata initial_role
  fi
fi

# In case of frontend upgrade, locales and statics should be regenerated
python manage.py compilemessages
python manage.py collectstatic --noinput

# Automatically replace "TAIGA_HOSTNAME" with the environment variable
sed -i "s/TAIGA_HOSTNAME/$TAIGA_HOSTNAME/g" /taiga/conf.json
sed -i "s/DEBUG_STATE/$DEBUG/g" /taiga/conf.json
sed -i "s/ALLOW_PUBLIC_REGISTRATION/$PUBLIC_REGISTER_ENABLED/g" /taiga/conf.json

# convert to lowercase
LDAP_ENABLED="$(echo $LDAP_ENABLED | sed -e 's/\(.*\)/\L\1/')"
if [ "$LDAP_ENABLED" = "true" ]; then
  sed -i 's/LOGIN_FORM_TYPE/"loginFormType": "ldap",/g' /taiga/conf.json
else
  sed -i 's/LOGIN_FORM_TYPE//g' /taiga/conf.json
fi

# List of plugin values for contribPlugins
PLUGINS=()

# ToDo: write additional plugin specific options into conf.json
SLACK_ENABLED="$(echo $SLACK_ENABLED | sed -e 's/\(.*\)/\L\1/')"
if [ "$SLACK_ENABLED" = "true" ]; then
  PLUGINS+=('/plugins/slack/slack.json')
fi

if [ -n "$PLUGINS" ]; then
  # Return quoted comma seperated list
  CONTRIB_PLUGINS=$(printf ',"%s"' "${PLUGINS[@]}")
  
  # Ignore first character
  sed -i "s|CONTRIB_PLUGINS|${CONTRIB_PLUGINS:1}|g" /taiga/conf.json
else
  sed -i 's/CONTRIB_PLUGINS//g' /taiga/conf.json
fi

# Look to see if we should set the "eventsUrl"
if [ ! -z "$RABBIT_PORT_5672_TCP_ADDR" ]; then
  echo "Enabling Taiga Events"
  sed -i "s/eventsUrl\": null/eventsUrl\": \"ws:\/\/$TAIGA_HOSTNAME\/events\"/g" /taiga/conf.json
  mv /etc/nginx/taiga-events.conf /etc/nginx/conf.d/default.conf
fi

# Convert vars to lowercase
TAIGA_SSL_BY_REVERSE_PROXY="$(echo $TAIGA_SSL_BY_REVERSE_PROXY | sed -e 's/\(.*\)/\L\1/')"
TAIGA_SSL="$(echo $TAIGA_SSL | sed -e 's/\(.*\)/\L\1/')"

# Handle enabling/disabling SSL
if [ "$TAIGA_SSL_BY_REVERSE_PROXY" = "true" ]; then
  echo "Enabling external SSL support! SSL handling must be done by a reverse proxy or a similar system"
  sed -i "s/http:\/\//https:\/\//g" /taiga/conf.json
  sed -i "s/ws:\/\//wss:\/\//g" /taiga/conf.json
elif [ "$TAIGA_SSL" = "true" ]; then
  echo "Enabling SSL support!"
  sed -i "s/http:\/\//https:\/\//g" /taiga/conf.json
  sed -i "s/ws:\/\//wss:\/\//g" /taiga/conf.json
  mv /etc/nginx/ssl.conf /etc/nginx/conf.d/default.conf
elif grep -q "wss://" "/taiga/conf.json"; then
  echo "Disabling SSL support!"
  sed -i "s/https:\/\//http:\/\//g" /taiga/conf.json
  sed -i "s/wss:\/\//ws:\/\//g" /taiga/conf.json
fi

# Start nginx service (need to start it as background process)
# nginx -g "daemon off;"
service nginx start

# Start gunicorn  server
exec "$@"
