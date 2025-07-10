#!/bin/bash

SETTING_FILE="./settings.ini"
SCRIPT_PATH=$(readlink -f "$0" | xargs dirname)
SETTING_FILE="${SCRIPT_PATH}/settings.ini"

TOPIC=$(git config -f $SETTING_FILE pubsub.topic || echo 'tag_media')


if [ ! -f "request.json" ]; then
    echo "Error: request.json not found."
    exit 1
fi

# Publish the raw content of request.json as the message.
# The gcloud CLI and Pub/Sub system handle the necessary base64 encoding.
gcloud pubsub topics publish $TOPIC --message "$(cat request.json)"
