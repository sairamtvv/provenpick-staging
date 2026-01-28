#!/bin/bash
cd /home/sai/Desktop/Projects_and_Folders/my_code/provenpick-staging
source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
export $(cat .env | grep -v '^#' | xargs)
python backend/main.py > /tmp/backend.log 2>&1 &
echo $! > backend.pid
