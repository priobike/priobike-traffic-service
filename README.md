`Archive notice: service is no longer used, as there were some API changes and we decided not to maintain this service further.`

# priobike-traffic-service

This repo contains a service that predicts the traffic for hamburg by regularly fetching data from the ["Verkehrslage Hamburg"](https://api.hamburg.de/datasets/v1/verkehrslage) API. Predictions are created by calculating the average value for each hour of the day if possible. Historical data is strored up to 6 weeks.

[Learn more about PrioBike](https://github.com/priobike)

## Quickstart

The easiest way to run priobike-traffic-service is to use the contained `docker-compose`:
```
docker-compose up
```

### Configuration

The service is configured using environment variables. The following variables are available:

#### Manager

- `WORKER_HOST` The host of the worker.
- `WORKER_PORT` The port of the worker.
- `WORKER_BASIC_AUTH_USER` The username for the basic auth.
- `WORKER_BASIC_AUTH_PASS` The pwassword for the basic auth.

#### Worker

- `MANAGER_HOSTNAME` The host of the worker.
- `MANAGER_PORT` The port of the worker.
- `BASIC_AUTH_USER` The username for the basic auth.
- `BASIC_AUTH_PASS` The pwassword for the basic auth.

We use basic auth such that only the authorized manager can update the worker with the /upload/prediction.json files.

## API and CLI

To upload a new `prediction.json` from the manager to the worker run a PUT request with basic authorization via:
`http://{worker_ip}:{port}/upload/{file_path}`

## What else to know
- This service can run in two modes: manager and worker. The worker mode is designed to face user traffic and can be scaled horizontally. Messages are synced between the worker and manager containers. See `docker-compose.yml` for an example setup.

## Contributing

We highly encourage you to open an issue or a pull request. You can also use our repository freely with the `MIT` license.

Every service runs through testing before it is deployed in our release setup. Read more in our [PrioBike deployment readme](https://github.com/priobike/.github/blob/main/wiki/deployment.md) to understand how specific branches/tags are deployed.

## Anything unclear?

Help us improve this documentation. If you have any problems or unclarities, feel free to open an issue.
