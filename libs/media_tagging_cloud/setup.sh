#!/bin/bash
#
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

SETTING_FILE="./settings.ini"
SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
SETTING_FILE="${SCRIPT_PATH}/settings.ini"

# changing the cwd to the script's containing folder so all paths inside can be local to it
# (important as the script can be called via absolute path and as a nested path)
pushd $SCRIPT_PATH > /dev/null

args=()
started=0
# pack all arguments into args array (except --settings)
for ((i=1; i<=$#; i++)); do
  if [[ ${!i} == --* ]]; then started=1; fi
  if [ ${!i} = "--settings" ]; then
    ((i++))
    SETTING_FILE=${!i}
  elif [ $started = 1 ]; then
    args+=("${!i}")
  fi
done
echo "Using settings from $SETTING_FILE"

PROJECT_ID=$(gcloud config get-value project 2> /dev/null)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="csv(projectNumber)" | tail -n 1)
REGION=$(git config -f $SETTING_FILE common.region || echo "europe-west1")


enable_apis() {
  gcloud services enable secretmanager.googleapis.com
  gcloud services enable artifactregistry.googleapis.com # required for Gen2 GCF
  gcloud services enable run.googleapis.com # required for Gen2 GCF
}


set_iam_permissions() {
  echo -e "${CYAN}Setting up IAM permissions...${NC}"
  declare -ar ROLES=(
    # For deploying Gen2 CF 'artifactregistry.repositories.list' and 'artifactregistry.repositories.get' permissions are required
    roles/artifactregistry.repoAdmin
    roles/iam.serviceAccountUser
    roles/secretmanager.secretAccessor
  )
  for role in "${ROLES[@]}"
  do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member=serviceAccount:$SERVICE_ACCOUNT \
      --role=$role \
      --condition=None
  done
}


create_secret() {
  local SECRET_NAME
  SECRET_NAME=$(_get_arg_value "--secret" "$@")
  local SECRET_VALUE
  SECRET_VALUE=$(_get_arg_value "--value" "$@")
  if [[ ! -n $SECRET_NAME ]]; then
    echo -e "${RED}Please provide a secret name via --secret argument${NC}"
    return 1
  fi
  if [[ ! -n $SECRET_VALUE ]]; then
    echo -e "${RED}Please provide a secret value via --value argument${NC}"
    return 1
  fi
  if gcloud secrets describe $SECRET_NAME >/dev/null 2>&1; then
      # Secret exists - add new version
      echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME --data-file=-
  else
      # Secret doesn't exist - create new
      echo -n "$SECRET_VALUE" | gcloud secrets create $SECRET_NAME --data-file=-
  fi
}


create_pubsub_topic() {
  # create completion topic
  TOPIC=$(git config -f $SETTING_FILE workflows.topic || echo "tag_media")
  TOPIC_EXISTS=$(gcloud pubsub topics list --filter="name.scope(topic):'$TOPIC'" --format="get(name)")
  if [[ ! -n $TOPIC_EXISTS ]]; then
    gcloud pubsub topics create $TOPIC
  fi
}


deploy_functions() {
  USE_SM=$(git config -f $SETTING_FILE functions.use-secret-manager || echo false)
  if [[ "$USE_SM" == "true" ]]; then
    USE_SM="--use-secret-manager"
  else
    USE_SM=""
  fi
  CF_MEMORY=$(git config -f $SETTING_FILE functions.memory || echo '512MB')
  if [[ -n $CF_MEMORY ]]; then
    CF_MEMORY="--memory=$CF_MEMORY"
  fi

  local set_secret
  if [[ $USE_SM ]]; then
    set_secret="--set-secrets GEMINI_API_KEY=gemini-api-key:latest"
  fi
  local trigger
  trigger=$(_get_arg_value "--trigger" "$@" || git config -f $SETTING_FILE functions.trigger)
  if [[ -z $trigger ]]; then
    trigger="http"
  fi
  local topic
  topic=$(_get_arg_value "--topic" "$@" || git config -f $SETTING_FILE pubsub.topic)

  local trigger_flags
  local timeout
  if [[ "$trigger" == "http" ]]; then
    trigger_flags="--trigger-http --no-allow-unauthenticated"
    timeout="--timeout=3600s"
  elif [[ "$trigger" == "pubsub" ]]; then
    if [[ -z $topic ]]; then
      echo -e "${RED}Please provide a topic via --topic argument${NC}"
      return 1
    fi
    create_pubsub_topic
    trigger_flags="--trigger-topic=$topic"
    timeout="--timeout=540s"
  else
    echo -e "${RED}Unsupported trigger type: $trigger${NC}"
    return 1
  fi

  gcloud functions deploy media_tagging \
      $trigger_flags \
      --entry-point=main \
      --runtime=python311 \
      $timeout \
      $CF_MEMORY \
      --region=$REGION \
      --quiet \
      --gen2 \
      $set_secret \
      --source=.
  return $?
}


deploy_all() {
  enable_apis || return $?
  set_iam_permissions $@ || return $?
  deploy_functions $@ || return $?
}


_get_arg_value() {
  local arg_name=$1
  shift
  for ((i=1; i<=$#; i++)); do
    if [ ${!i} = "$arg_name" ]; then
      # Check if this is the last argument or if next argument starts with - or --
      ((next=i+1))
      if [ $next -gt $# ] || [[ "${!next}" == -* ]]; then
        # This is a flag without value
        echo "true"
        return 0
      else
        # This is a value argument
        echo ${!next}
        return 0
      fi
    fi
  done
  return 1
}


_list_functions() {
  # list all functions in this file not starting with "_"
  declare -F | awk '{print $3}' | grep -v "^_"
}


if [[ $# -eq 0 ]]; then
  echo "USAGE: $0 target1 target2 ... [--settings /path/to/settings.ini]"
  echo "  where supported targets:"
  _list_functions
else
  for i in "$@"; do
    if [[ $i == --* ]]; then
      break
    fi
    if declare -F "$i" > /dev/null; then
      "$i" ${args[@]}
      exitcode=$?
      if [ $exitcode -ne 0 ]; then
        echo -e "${RED}Breaking script as command '$i' failed${NC}"
        exit $exitcode
      fi
    else
      echo -e "${RED}Function '$i' does not exist.${NC}"
      exit -1
    fi
  done
fi

popd > /dev/null
