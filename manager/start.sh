#!/bin/bash

set -e

# Print env vars to file
env > /app/env.txt

# Install cronjobs
env | crontab -
crontab -l | { cat; echo "0 * * * * python3 /app/fetch-traffic-data.py >> /var/log/cron-fetch.log 2>&1"; } | crontab -
crontab -l | { cat; echo "1 * * * * python3 /app/predict-traffic.py /usr/share/nginx/html/prediction.json >> /var/log/cron-fetch.log 2>&1"; } | crontab - 

# Execute the script once
python3 /app/fetch-traffic-data.py
python3 /app/predict-traffic.py /usr/share/nginx/html/prediction.json

# Start cron
service cron start

# Check if cron is running
if ps aux | grep '[c]ron' > /dev/null; then
  echo "Cron is running"
else
  echo "Cron failed to start"
  exit 1
fi

# Start nginx
nginx -g "daemon off;"