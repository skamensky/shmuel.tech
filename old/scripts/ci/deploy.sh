#!/usr/bin/env bash
# TODO make sure we're running in the root of the repo

set -e
export STAGE=prod
source ./scripts/env/inject-environment.sh

export root_project_dir="$(pwd)"
trap "cd \"$root_project_dir\"" EXIT

START_DOCKER="true"
# useful when dev work required deployment and we don't want
if [ "$1" == "--from-local" ]; then
  echo "deploying from local"
  shift
else
  rm -rf /tmp/deploy-skam-over-ssh
  mkdir /tmp/deploy-skam-over-ssh
  cd /tmp/deploy-skam-over-ssh
  git clone https://github.com/skamensky/skam.dev --depth 1
  cd skam.dev
  cp "$root_project_dir/scripts/env/secrets.env" ./scripts/env/secrets.env
fi

if [ "$1" == "--no-start" ]; then
  START_DOCKER="false"
  shift
fi

ssh_key_full_path="$HOME/$SSH_KEY_LOCATION_FROM_HOME"
{
  # thanks to https://stackoverflow.com/a/15373763/4188138 from the ":- .gitignore" trick
  rsync -Pav --filter=':- .gitignore' --exclude='.git/' --delete --delete-excluded -e "ssh -i $ssh_key_full_path" . ubuntu@$SSH_IP:/home/ubuntu/skam.dev
  scp -i "$ssh_key_full_path" "scripts/env/secrets.env" ubuntu@$SSH_IP:/home/ubuntu/skam.dev/scripts/env/secrets.env

} 1>/dev/null
echo "files deployed to remote server"

if [ "$START_DOCKER" == "true" ]; then
  ssh -i "$ssh_key_full_path" "ubuntu@$SSH_IP" -t "export STAGE=prod; cd skam.dev && /bin/bash ./scripts/docker/ops.sh up"
else
  echo ' "--no-start" was specified. Skipping docker rebuild/start'
fi
