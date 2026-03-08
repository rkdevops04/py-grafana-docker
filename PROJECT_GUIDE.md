# Project Guide: URLs, Setup, and Learning

## 1. What this project does
This project runs a Flask application with observability tooling:
- App endpoint (Flask)
- Metrics endpoint (Prometheus format)
- Prometheus for metric scraping and querying
- Grafana for dashboards
- Jaeger for distributed tracing

## 2. URLs (Docker Compose)
When running with `docker compose up -d --build`:
- App: `http://localhost:5000/`
- Metrics: `http://localhost:8000/metrics`
- Grafana: `http://localhost:3000/`
- Prometheus: `http://localhost:9090/`
- Jaeger: `http://localhost:16686/`
- Rancher UI (optional profile): `https://localhost:8443/`

### If you are in GitHub Codespaces
Use forwarded URLs:
- `https://<codespace-name>-5000.app.github.dev`
- `https://<codespace-name>-8000.app.github.dev/metrics`
- `https://<codespace-name>-3000.app.github.dev`
- `https://<codespace-name>-9090.app.github.dev`
- `https://<codespace-name>-16686.app.github.dev`
- `https://<codespace-name>-8443.app.github.dev`

Find your current Codespace name:
```bash
echo "$CODESPACE_NAME"
```

Generate all forwarded URLs for this project automatically:
```bash
echo "App: https://${CODESPACE_NAME}-5000.app.github.dev"
echo "Metrics: https://${CODESPACE_NAME}-8000.app.github.dev/metrics"
echo "Grafana: https://${CODESPACE_NAME}-3000.app.github.dev"
echo "Prometheus: https://${CODESPACE_NAME}-9090.app.github.dev"
echo "Jaeger: https://${CODESPACE_NAME}-16686.app.github.dev"
echo "Rancher: https://${CODESPACE_NAME}-8443.app.github.dev"
```

## 3. Login credentials
Grafana credentials (set in `docker-compose.yml`):
- Username: `admin`
- Password: `admin`

## 4. Step-by-step instructions
1. Install and start:
   ```bash
   docker compose up -d --build
   ```
2. Generate traffic to the app:
   ```bash
   curl http://localhost:5000/
   curl http://localhost:5000/
   curl http://localhost:5000/
   ```
3. Check metrics page:
   - Open `http://localhost:8000/metrics`
4. Check Prometheus:
   - Open `http://localhost:9090/graph`
   - Run queries from section 5
5. Check Grafana:
   - Open `http://localhost:3000/`
   - Login with `admin/admin`
   - Open dashboard: `Flask Observability Dashboard`
   - Open dashboard: `K8s Namespace & Pod Infra Metrics`
6. Check Jaeger:
   - Open `http://localhost:16686/search`
   - Choose service `flask-app`
   - Click `Find Traces`

7. Optional: Start Rancher UI from this project:
   ```bash
   docker compose --profile rancher up -d rancher
   ```
   - Open `https://localhost:8443/` (or Codespaces forwarded `8443` URL).
   - Wait a few minutes for first-time bootstrap.
   - Print Rancher URL + bootstrap password in one command:
   ```bash
   RURL="https://localhost:8443"; [ -n "$CODESPACE_NAME" ] && RURL="https://${CODESPACE_NAME}-8443.app.github.dev"; echo "Rancher URL: $RURL"; echo -n "Bootstrap Password: "; docker logs $(docker compose ps -q rancher) 2>&1 | grep -i "Bootstrap Password" | tail -n 1 | sed 's/.*Bootstrap Password: //'
   ```
   - Get bootstrap password:
   ```bash
   docker logs $(docker compose ps -q rancher) 2>&1 | grep -i "Bootstrap Password" | tail -n 1
   ```
   - Username is `admin`.

## 5. Prometheus queries to use
- `up`
- `up{job="flask-app"}`
- `request_duration_seconds_count`
- `rate(request_duration_seconds_count[1m])`
- `request_duration_seconds_sum`
- `rate(request_duration_seconds_sum[5m]) / rate(request_duration_seconds_count[5m])`

## 6. Jaeger search values
In Jaeger Search page:
- Service: `flask-app`
- Operation: `GET /` (if available)
- Lookback: `Last 1 hour`
- Min Duration: optional

If no traces appear:
- Ensure app container is running
- Send app traffic (several requests to `/`)
- Refresh Jaeger search

## 7. What we need to do (operational checklist)
- Build and run containers
- Verify each URL opens
- Generate test traffic
- Validate metrics in Prometheus
- Validate dashboards in Grafana
- Validate traces in Jaeger
- Capture logs when debugging

Useful commands:
```bash
docker compose ps
docker compose logs -f flask-app
docker compose logs -f prometheus
docker compose logs -f grafana
docker compose logs -f jaeger
docker compose logs -f rancher
docker compose down
```

## 8. What we learn from this project
- How to containerize a Python Flask app
- How to expose Prometheus metrics from app code
- How Prometheus scraping works (`prometheus.yml` target)
- How Grafana dashboards are provisioned from files
- How OpenTelemetry tracing data reaches Jaeger
- How to troubleshoot observability stacks with logs, queries, and traces

## 9. Rancher note
Rancher can be started from this project using the optional compose profile:
```bash
docker compose --profile rancher up -d rancher
```

If Rancher does not start in your environment, it is usually due to Docker privilege/runtime limits (common in restricted cloud dev containers).
