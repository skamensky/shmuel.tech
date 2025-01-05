#!/usr/bin/env bash

# TODO remove script_dir everwhere, make a script that ensures we are running from root of repo. If not, fail
# TODO write script to deploy start ec2 image, and attach volume
set -e
source "scripts/env/inject-environment.sh"

# for copy and paste purposes:
export DOCKER_PROJECT_NAME='skam'

USAGE="usage: ./scripts/docker/ops.sh [up|down|build]"
COMMAND=$1
ENV_DIR="scripts/env"
if [ $# -eq 0 ]; then
    echo "$USAGE"
    exit 1
fi

# see https://stackoverflow.com/a/69519102/4188138
export COMPOSE_COMPATIBILITY=true

if [[ "$STAGE" == "prod" ]]; then
   DOCKER_COMPOSE_FILE="docker-compose-prod.yaml"
   else
    DOCKER_COMPOSE_FILE="docker-compose-dev.yaml"
fi

function build(){
  docker compose --project-name "$DOCKER_PROJECT_NAME" --file $DOCKER_COMPOSE_FILE --profile init build
}

function up(){
  down
  build
  start_up_command_base="docker compose --project-name ${DOCKER_PROJECT_NAME} --env-file ${ENV_DIR}/.effective-env.env --file ${DOCKER_COMPOSE_FILE}"
  start_up_command="$start_up_command_base up --remove-orphans"
  # when using compose run, we need to specify the command and --service-ports to make use of the ports specified in the docker compose file
  start_up_command_init="$start_up_command_base --profile init run --service-ports docker_dns_certbot_init init"

  if [[ "$STAGE" == "prod" ]]; then
     start_up_command="${start_up_command} --detach && docker system prune --force"
  fi

  set -x
  $start_up_command_init
  down
  echo "$start_up_command"
  # need to eval here since for some reason it's not working with --force at the end...
  eval $start_up_command
  set +x
}

function down(){
  set -x
  docker compose --project-name $DOCKER_PROJECT_NAME --file $DOCKER_COMPOSE_FILE down
  set +x
}

case $COMMAND in
    up)
        up
        ;;
    down)
        down
        ;;
    build)
        build
        ;;
    *)
        echo "$USAGE"
        exit 1
        ;;
esac
