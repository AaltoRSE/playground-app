#!/bin/bash -x
cd /home/ai4eu
. grpc/bin/activate
cd playground-app/
export SECRET_KEY=$(uuidgen)
# nohup python3 https_app.py > playground.log 2>&1 &
gunicorn -w 20 -b 0.0.0.0:443 --timeout 300 --keyfile /etc/letsencrypt/live/playground.ki-lab.nrw/privkey.pem --certfile  /etc/letsencrypt/live/playground.ki-lab.nrw/fullchain.pem  gunicorn_app:app
