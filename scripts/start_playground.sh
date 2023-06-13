#!/bin/bash -x
cd /home/ai4eu
. grpc/bin/activate
cd playground-app/
export SECRET_KEY=$(uuidgen)
# nohup python3 https_app.py > playground.log 2>&1 &
HTTPS_CHAIN=$(jq -r '.https_chain' config.json)
HTTPS_KEY=$(jq -r '.https_key' config.json)
gunicorn -w 20 -b 0.0.0.0:443 --timeout 300 --keyfile $HTTPS_KEY --certfile $HTTPS_CHAIN  gunicorn_app:app