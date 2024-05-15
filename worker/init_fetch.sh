curl "http://$MANAGER_HOSTNAME:$MANAGER_PORT/prediction.json" > /app/data/prediction.json
# If it fails, this means that the manager is not ready yet. We don't need to try again because the manager is going to push the first version of the prediction file to the workers.
if [ $? -ne 0 ]; then
    echo "Failed to fetch prediction.json from manager. This is expected if the manager is not ready yet."
    exit 0
else
    echo "Fetched prediction.json from manager."
fi