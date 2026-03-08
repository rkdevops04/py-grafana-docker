# Quick Manual (Copy-Paste)

## 0. Install Missing Tools (Only if command not found)

Check:
```bash
docker --version
docker compose version
python3 --version
pip3 --version
kubectl version --client
git --version
curl --version
jq --version
```

Ubuntu/Codespaces install:
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release git jq python3 python3-pip python3-venv apt-transport-https
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin kubectl
sudo usermod -aG docker $USER
newgrp docker
```

## 1. Start Core Stack

```bash
cd /workspaces/py-grafana-docker
docker compose up -d --build
docker compose ps
```

## 2. Open URLs

### Local
```bash
echo "App: http://localhost:5000/"
echo "Metrics: http://localhost:8000/metrics"
echo "Grafana: http://localhost:3000/"
echo "Prometheus: http://localhost:9090/"
echo "Jaeger: http://localhost:16686/"
```

### GitHub Codespaces
```bash
echo "App: https://${CODESPACE_NAME}-5000.app.github.dev"
echo "Metrics: https://${CODESPACE_NAME}-8000.app.github.dev/metrics"
echo "Grafana: https://${CODESPACE_NAME}-3000.app.github.dev"
echo "Prometheus: https://${CODESPACE_NAME}-9090.app.github.dev"
echo "Jaeger: https://${CODESPACE_NAME}-16686.app.github.dev"
echo "Rancher: https://${CODESPACE_NAME}-8443.app.github.dev"
```

## 3. Grafana Login

```text
URL: http://localhost:3000 (or forwarded 3000 URL)
Username: admin
Password: admin
```

## 4. Generate App Traffic

```bash
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/
```

## 5. Prometheus Quick Checks

```bash
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | [.labels.job,.scrapeUrl,.health] | @tsv'
```

```promql
up
up{job="flask-app"}
rate(request_duration_seconds_count[1m])
rate(request_duration_seconds_sum[5m]) / rate(request_duration_seconds_count[5m])
```

## 6. Jaeger Quick Check

```text
URL: http://localhost:16686/search
Service: flask-app
```

## 7. Start Rancher (Optional)

```bash
docker compose --profile rancher up -d rancher
docker compose ps rancher
```

```bash
docker logs $(docker compose ps -q rancher) 2>&1 | grep -i "Bootstrap Password" | tail -n 1
```

```text
URL: https://localhost:8443 (or forwarded 8443 URL)
Username: admin
Password: bootstrap password from command above
```

## 8. Deploy to Kubernetes (Rancher k3s)

```bash
kubectl apply -k k8s
```

```bash
docker exec py-grafana-docker-rancher-1 kubectl -n observability-demo get pods -o wide
docker exec py-grafana-docker-rancher-1 kubectl get nodes -o wide
```

## 9. If Pod Fails with ImagePullBackOff

```bash
docker save flask-app:latest | docker exec -i py-grafana-docker-rancher-1 ctr -n k8s.io images import -
docker exec py-grafana-docker-rancher-1 kubectl -n observability-demo delete pod -l app=flask-app
docker exec py-grafana-docker-rancher-1 kubectl -n observability-demo rollout status deploy/flask-app --timeout=180s
```

## 10. Enable K8s Metrics for Grafana Dashboard

```bash
docker exec py-grafana-docker-rancher-1 kubectl apply -k 'github.com/kubernetes/kube-state-metrics/examples/standard?ref=v2.13.0'
```

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

```bash
docker compose restart prometheus grafana
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | [.labels.job,.scrapeUrl,.health] | @tsv'
```

```promql
up{job="kube-state-metrics"}
count(kube_node_info)
count(kube_pod_info)
count(kube_pod_info) by (namespace)
sum(kube_pod_container_resource_requests{resource="cpu"}) by (namespace)
sum(kube_pod_container_resource_requests{resource="memory"}) by (namespace)
```

## 11. Logs and Restart

```bash
docker compose logs -f flask-app
docker compose logs -f prometheus
docker compose logs -f grafana
docker compose logs -f jaeger
docker compose logs -f rancher
```

```bash
docker compose restart flask-app
docker compose restart prometheus grafana
docker compose restart rancher
```

## 12. Stop and Cleanup

```bash
docker compose down
docker compose down -v
```
