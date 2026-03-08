# py-grafana-docker

## Project Overview
This project encapsulates everything you need to run Grafana in a Docker container effortlessly. It includes a preconfigured setup with various options to customize your Grafana installation.

## Table of Contents
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Requirements
- Docker
- Docker Compose (if using docker-compose.yml)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/rkdevops04/py-grafana-docker.git
   cd py-grafana-docker
   ```
2. Build the Docker image:
   ```bash
   docker-compose build
   ```

## Usage
- To run the application:
  ```bash
  docker-compose up
  ```
- Access Grafana:
  Open your browser and go to `http://localhost:3000`

## Testing
- Install dependencies and run tests:
  ```bash
  pip install -r requirements.txt
  pytest
  ```

## Rancher (Kubernetes): App, Metrics, and Logs

This repo includes Kubernetes manifests under `k8s/` for running the Flask app in a Rancher-managed cluster.

### 1. Build and push image
Update the image in `k8s/flask-app.yaml` to your registry tag (example: `docker.io/<user>/flask-app:latest`) and push it:

```bash
docker build -t docker.io/<user>/flask-app:latest .
docker push docker.io/<user>/flask-app:latest
```

### 2. Deploy to Kubernetes

```bash
kubectl apply -k k8s
```

If Rancher Monitoring (Prometheus Operator) is installed, also apply:

```bash
kubectl apply -k k8s/monitoring
```

Set your public DNS host in `k8s/ingress.yaml` (`flask-app.example.com`) and adjust `ingressClassName` if your cluster uses a class other than `nginx`.

### 3. Verify app

```bash
kubectl -n observability-demo get pods,svc
kubectl -n observability-demo port-forward svc/flask-app 5000:5000 8000:8000
```

Then open:
- `http://127.0.0.1:5000/`
- `http://127.0.0.1:8000/metrics`

If Ingress is configured and DNS points to your ingress controller, open:
- `http://flask-app.example.com/`

### 4. View logs in Rancher
- In Rancher UI: `Cluster` -> `Projects/Namespaces` -> `observability-demo` -> `Workloads` -> `flask-app` -> `Pod` -> `Logs`.
- CLI alternative:

```bash
kubectl -n observability-demo logs deploy/flask-app -f
```

### 5. View metrics in Rancher
- In Rancher UI: `Cluster` -> `Monitoring` -> `Explore` (or Grafana) and query:
  - `request_duration_seconds_count`
  - `request_duration_seconds_sum`
  - `up{namespace="observability-demo"}`
- If metrics are missing, confirm scrape target health in Prometheus and verify `Service` annotations / `ServiceMonitor` were applied.

## Configuration
- Customize the `docker-compose.yml` file to set up different databases, Grafana settings, and more.

## Contributing
We welcome contributions! Please fork the repo and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For additional questions or support, please reach out to rkdevops04.

## Quick Start Guide
- See `PROJECT_GUIDE.md` for all URLs, credentials, Prometheus queries, Jaeger search steps, and project learning outcomes.