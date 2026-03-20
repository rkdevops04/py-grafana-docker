# Manual Implementation Guide

This guide explains how to implement and run the full project manually, including:
- Flask app
- Prometheus metrics
- Grafana dashboards
- Jaeger tracing
- Rancher (optional)
- Kubernetes deployment path

## 1. Prerequisites

## 1.1 System requirements
- Linux/macOS/Windows with Docker support
- 4+ CPU, 8+ GB RAM recommended if running Rancher
- Internet access to pull container images

## 1.2 Install tools

### Docker and Docker Compose
- Verify install:
```bash
docker --version
docker compose version
```

If `docker: command not found` or `docker compose` is unavailable (Ubuntu/Codespaces):
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

If you are on macOS/Windows, install Docker Desktop and then verify:
```bash
docker --version
docker compose version
```

### Python (for local tests)
- Verify:
```bash
python3 --version
pip3 --version
```

If missing on Ubuntu/Codespaces:
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
python3 --version
pip3 --version
```

### kubectl (needed for k8s path)
- Verify:
```bash
kubectl version --client
```

If missing on Ubuntu/Codespaces:
```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl
kubectl version --client
```

### Git, curl, jq (used by commands in this repo)
- Verify:
```bash
git --version
curl --version
jq --version
```

If missing on Ubuntu/Codespaces:
```bash
sudo apt-get update
sudo apt-get install -y git curl jq
```

## 1.3 Clone repository
```bash
git clone https://github.com/rkdevops04/py-grafana-docker.git
cd py-grafana-docker
```

## 2. Project Configurations

## 2.1 Docker Compose services
Configured in `docker-compose.yml`:
- `flask-app` on ports `5000` and `8000`
- `prometheus` on port `9090`
- `grafana` on port `3000`
- `jaeger` on port `16686` and OTLP gRPC `4317`
- `rancher` on ports `8080/8443` (optional profile)

## 2.2 Prometheus scrape config
Configured in `monitoring/prometheus.yml`:
- Job `flask-app` scraping `flask-app:8000`
- Job `kube-state-metrics` scraping `rancher:30080`

## 2.3 Grafana provisioning
- Datasource: `monitoring/grafana/provisioning/datasources/datasource.yml`
- Dashboard provider: `monitoring/grafana/provisioning/dashboards/provider.yml`
- Dashboards directory: `monitoring/grafana/dashboards/`

## 3. Run Full Stack with Docker Compose

## 3.1 Start core services
```bash
docker compose up -d --build
```

## 3.2 Verify container health
```bash
docker compose ps
```

## 3.3 Service URLs (local)
- Flask app: `http://localhost:5000/`
- Flask metrics: `http://localhost:8000/metrics`
- Grafana: `http://localhost:3000/`
- Prometheus: `http://localhost:9090/`
- Jaeger: `http://localhost:16686/`

## 3.4 Service URLs (GitHub Codespaces)
```bash
echo "App: https://${CODESPACE_NAME}-5000.app.github.dev"
echo "Metrics: https://${CODESPACE_NAME}-8000.app.github.dev/metrics"
echo "Grafana: https://${CODESPACE_NAME}-3000.app.github.dev"
echo "Prometheus: https://${CODESPACE_NAME}-9090.app.github.dev"
echo "Jaeger: https://${CODESPACE_NAME}-16686.app.github.dev"
echo "Rancher: https://${CODESPACE_NAME}-8443.app.github.dev"
```

## 4. Login and Access Details

## 4.1 Grafana login
- URL: `http://localhost:3000` (or forwarded `3000` URL)
- Username: `admin`
- Password: `admin`

## 4.2 Jenkins login (optional)
- URL (local): `http://localhost:8088/`
- URL (Codespaces tunnel example): `https://<codespace-name>-8088.app.github.dev/`
- Default container name used in this repo: `jenkins-local`

Check Jenkins availability:
```bash
curl -I http://localhost:8088/
```

## 4.3 Rancher login (optional)
Start Rancher:
```bash
docker compose --profile rancher up -d rancher
```

Get bootstrap password:
```bash
docker logs $(docker compose ps -q rancher) 2>&1 | grep -i "Bootstrap Password" | tail -n 1
```

- URL: `https://localhost:8443` (or forwarded `8443` URL)
- Username: `admin`
- Password: bootstrap password from command above

## 5. Validate Observability Components

## 5.1 Generate traffic to Flask
```bash
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/
```

## 5.2 Check Prometheus targets
Open Prometheus `Status -> Targets` or run:
```bash
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | [.labels.job,.scrapeUrl,.health] | @tsv'
```

Expected jobs:
- `flask-app`
- `kube-state-metrics` (if Rancher+k8s metrics path is enabled)

## 5.3 Open Grafana dashboards
- `Flask Observability Dashboard`
- `K8s Namespace & Pod Infra Metrics`

## 5.4 Verify Jaeger traces
- Open `http://localhost:16686/search`
- Service: `flask-app`
- Click `Find Traces`

## 6. Prometheus Queries You Can Use

```promql
up
up{job="flask-app"}
up{job="kube-state-metrics"}
rate(request_duration_seconds_count[1m])
rate(request_duration_seconds_sum[5m]) / rate(request_duration_seconds_count[5m])
count(kube_node_info)
count(kube_pod_info)
count(kube_pod_info) by (namespace)
sum(kube_pod_container_resource_requests{resource="cpu"}) by (namespace)
sum(kube_pod_container_resource_requests{resource="memory"}) by (namespace)
```

## 7. Kubernetes Manual Deployment (Rancher Local k3s)

## 7.1 Apply manifests
```bash
kubectl apply -k k8s
```

This creates:
- Namespace `observability-demo`
- Deployment and Service `flask-app`
- Ingress `flask-app`

## 7.2 Verify deployment and node placement
```bash
kubectl -n observability-demo get pods -o wide
kubectl get nodes -o wide
```

## 7.3 If image pull fails (`ImagePullBackOff`)
The manifest uses `flask-app:latest`. If not in remote registry, import local image into Rancher container runtime:

```bash
docker save flask-app:latest | docker exec -i py-grafana-docker-rancher-1 ctr -n k8s.io images import -
docker exec py-grafana-docker-rancher-1 kubectl -n observability-demo delete pod -l app=flask-app
docker exec py-grafana-docker-rancher-1 kubectl -n observability-demo rollout status deploy/flask-app --timeout=180s
```

## 8. Kubernetes Metrics for Grafana Dashboard

If k8s dashboard panels are empty, install `kube-state-metrics` and expose it:

```bash
docker exec py-grafana-docker-rancher-1 kubectl apply -k 'github.com/kubernetes/kube-state-metrics/examples/standard?ref=v2.13.0'
```

Create NodePort service for Prometheus scrape:
```bash
cat <<'EOF' | docker exec -i py-grafana-docker-rancher-1 kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: kube-state-metrics-nodeport
  namespace: kube-system
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: kube-state-metrics
  ports:
  - name: http-metrics
    port: 8080
    targetPort: http-metrics
    nodePort: 30080
EOF
```

Prometheus must include:
```yaml
- job_name: kube-state-metrics
  static_configs:
    - targets:
        - rancher:30080
```

Reload monitoring services:
```bash
docker compose restart prometheus grafana
```

## 9. Common Operations

## 9.1 Logs
```bash
docker compose logs -f flask-app
docker compose logs -f prometheus
docker compose logs -f grafana
docker compose logs -f jaeger
docker compose logs -f rancher
```

## 9.2 Restart services
```bash
docker compose restart flask-app
docker compose restart prometheus grafana
docker compose restart rancher
```

## 9.3 Stop and cleanup
```bash
docker compose down
docker compose down -v
```

To stop every running Docker container on the host (including non-compose containers such as `jenkins-local`):

```bash
docker ps -q | xargs -r docker stop
```

## 9.4 Run updated `app.py` after code changes

If you edited `app.py` and want to run it directly from the repo (instead of the compose `flask-app` container), use:

```bash
cd /workspaces/py-grafana-docker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose stop flask-app
python app.py
```

If `.venv` already exists, use this quick rerun one-liner:

```bash
cd /workspaces/py-grafana-docker && source .venv/bin/activate && docker compose stop flask-app && python app.py
```

Verify in another terminal:

```bash
curl http://localhost:5000/
curl http://localhost:8000/metrics
```

For Codespaces URLs:

```bash
echo "App: https://${CODESPACE_NAME}-5000.app.github.dev"
echo "Metrics: https://${CODESPACE_NAME}-8000.app.github.dev/metrics"
```

When done testing direct run mode, switch back to compose-managed app:

```bash
docker compose up -d flask-app
```

## 10. Local Testing

Install dependencies and run tests:
```bash
pip install -r requirements.txt
pytest -q
```

## 11. Troubleshooting

## 11.1 Rancher URL not opening in Codespaces
- Ensure port `8443` is forwarded in Ports tab.
- Open the forwarded URL directly from Ports tab.
- If you get `www-authenticate: tunnel`, authenticate in browser with GitHub session.

## 11.2 `kubectl` TLS error against Rancher
If local `kubectl` context is not trusted, run kubectl inside Rancher container:
```bash
docker exec py-grafana-docker-rancher-1 kubectl get nodes
```

## 11.3 Grafana k8s dashboard empty
- Confirm Prometheus target `kube-state-metrics` is `up`.
- Confirm `kube_` metrics exist:
```bash
curl -s 'http://localhost:9090/api/v1/label/__name__/values' | jq -r '.data[]' | grep '^kube_' | head
```

## 11.4 Flask app pod not running on k8s
- Check events:
```bash
docker exec py-grafana-docker-rancher-1 kubectl -n observability-demo describe pod -l app=flask-app
```
- Resolve image pull as in section 7.3.

## 12. End-to-End Manual Checklist

1. Install Docker, Compose, kubectl, Python.
2. Clone repo and start core stack.
3. Verify Flask, Prometheus, Grafana, Jaeger URLs.
4. Login to Grafana (`admin/admin`).
5. Start Rancher profile and login with bootstrap password.
6. Apply k8s manifests and verify pod/node.
7. Enable kube-state-metrics scrape and restart Prometheus/Grafana.
8. Validate Grafana dashboards and Prometheus queries.
9. Capture logs for any failing component.
