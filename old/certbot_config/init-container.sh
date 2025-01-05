#!/bin/bash
set -e


USAGE="usage: ./init-container.sh [init|renew]"
export CERTBOT_DATA_DIR="/mnt/cert_data/certbot"
export INIT_SENTINEL_FILE="$CERTBOT_DATA_DIR/initial-setup-complete.sentinel"

# unfortunately, docker compose 3 syntax stopped supporting conditional startup order. See
# https://docs.docker.com/compose/startup-order/ and https://github.com/docker/compose/issues/4305
# therefore we need to communicate directly between the images
function signal_nginx_exit_status(){
  if [ "$?" -eq 0 ]; then
    status="OK"
  else
    status="ERROR, certbot exited with status $?"
  fi
  echo "$status" > /mnt/cert_data/status_for_nginx
}
trap signal_nginx_exit_status EXIT

if [ "$STAGE" == "dev" ]; then
  echo "Currently in dev mode. No need to run certbot. Exiting the container"
  exit 0
fi


# TODO add ,shmuelkamensky.com,www.shmuelkamensky.com
DOMAINS="skam.dev,www.skam.dev"

EMAIL="shmuelkamensky@gmail.com"
function init_certbot(){
  if [ -f "$INIT_SENTINEL_FILE" ]; then
    echo "first_time_challenges has run in the past. Skipping first time challenges."
    exit 0
  else
    echo "Cert never created. Initializing first time first_time_challenges"
  fi

  mkdir -p /mnt/cert_data/logs

  rm -rf /mnt/cert_data/certbot/live/skam.dev
  mkdir -p /mnt/cert_data/certbot/conf/
  certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --no-eff-email \
    --domains $DOMAINS \
    --preferred-challenges http-01 \
    --http-01-port 80 \
    --logs-dir /mnt/cert_data/logs \
    --config-dir $CERTBOT_DATA_DIR \
    --webroot-path="$CERTBOT_DATA_DIR/conf" \
    --key-path "$CERTBOT_DATA_DIR/conf/skam.dev/privkey.pem" \
    --fullchain-path "$CERTBOT_DATA_DIR/conf/skam.dev/fullchain.pem" \
    && touch $INIT_SENTINEL_FILE
    echo "OK" > /mnt/cert_data/status_for_nginx
}

function renew_every_12_hours(){
  while true
  do
      echo "Renewing cert"
      certbot renew --config-dir "$CERTBOT_DATA_DIR"
      sleep 12h
  done
}

case "$1" in
  init)
    init_certbot
    ;;
  renew)
    renew
    ;;
  *)
    echo "$USAGE" >&2
    exit 1
    ;;
esac