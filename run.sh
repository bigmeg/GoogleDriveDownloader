#!/bin/sh
PORT=$(awk -F "=" '/SERVER_PORT/ {print $2}' settings.ini | xargs)
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
sudo docker build $SCRIPTPATH -t gdd
sudo docker run  --entrypoint "/root/GoogleDriveDownloader/server.py" -d -p $PORT:$PORT \
  -v ~/Downloads/:/root/Downloads \
  -v $SCRIPTPATH:/root/GoogleDriveDownloader  \
  --restart unless-stopped gdd
