# AWS Deployment Guide (EC2, Security Rules, Ports, Load Balancer)

This guide explains how to run this project on AWS with practical options.

Project services in this repo:
- Flask app (`5000`)
- Prometheus metrics endpoint (`8000`)
- Grafana (`3000`)
- Prometheus (`9090`)
- Jaeger UI (`16686`)
- Rancher optional (`8443`)

## 1. Architecture Options

## Option A: Single EC2 (Fastest)
- Run `docker compose` on one EC2 instance.
- Expose only required ports using Security Group.
- Best for demo, lab, internal testing.

## Option B: EC2 + ALB (Recommended for public app)
- Keep observability tools private.
- Expose only Flask app via ALB (HTTP/HTTPS).
- Better for controlled public access.

## Option C: EKS (Kubernetes production path)
- Use EKS + AWS Load Balancer Controller.
- Use `k8s/` manifests from this repo.
- Best for scalable production environments.

## 2. AWS Prerequisites

- AWS account
- IAM user/role with EC2/VPC/ELB permissions
- Key pair for EC2 SSH access
- VPC + public subnet(s)

Optional:
- Route53 hosted zone
- ACM certificate (for HTTPS on ALB)

## 3. EC2 Instance Setup (Option A / B base)

## 3.1 Launch instance
Recommended:
- AMI: Ubuntu 22.04/24.04 or Amazon Linux 2023
- Type: `t3.medium` minimum for full stack
- Storage: 20+ GB

## 3.2 Security Group rules

Minimum inbound rules for direct access:
- `22/tcp` from your IP only (SSH)
- `5000/tcp` from trusted CIDRs (Flask app)
- `3000/tcp` from trusted CIDRs (Grafana)
- `9090/tcp` from trusted CIDRs (Prometheus)
- `16686/tcp` from trusted CIDRs (Jaeger)
- `8443/tcp` from trusted CIDRs (Rancher, optional)

Metrics notes:
- `8000/tcp` is app metrics; do not expose publicly unless needed.
- Prefer internal-only access for `8000`, `9090`, `3000`, and `16686`.

Outbound:
- Allow all outbound or at least `443` and `53`.

## 3.3 OS firewall (optional)
If using Ubuntu UFW:
```bash
sudo ufw allow OpenSSH
sudo ufw allow 5000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 9090/tcp
sudo ufw allow 16686/tcp
sudo ufw allow 8443/tcp
sudo ufw enable
sudo ufw status
```

## 4. Install Docker and Compose on EC2

## Ubuntu
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

## Amazon Linux 2023
```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
newgrp docker
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
docker --version
docker compose version
```

## 5. Deploy the Project on EC2

```bash
git clone https://github.com/rkdevops04/py-grafana-docker.git
cd py-grafana-docker
docker compose up -d --build
docker compose ps
```

Health checks:
```bash
curl -f http://localhost:5000/
curl -f http://localhost:8000/metrics
curl -f http://localhost:9090/-/healthy
curl -f http://localhost:3000/api/health
curl -f http://localhost:16686/
```

## 6. Access and Login

- Flask: `http://<EC2_PUBLIC_IP>:5000/`
- Grafana: `http://<EC2_PUBLIC_IP>:3000/` (user/pass: `admin` / `admin`)
- Prometheus: `http://<EC2_PUBLIC_IP>:9090/`
- Jaeger: `http://<EC2_PUBLIC_IP>:16686/`

Optional Rancher:
```bash
docker compose --profile rancher up -d rancher
```
- Rancher URL: `https://<EC2_PUBLIC_IP>:8443/`
- Bootstrap password:
```bash
docker logs $(docker compose ps -q rancher) 2>&1 | grep -i "Bootstrap Password" | tail -n 1
```

## 7. Load Balancer Setup (Option B)

## 7.1 ALB for Flask app (recommended)

Create ALB:
- Scheme: internet-facing
- Subnets: at least 2 public subnets
- Security Group (ALB): allow `80` and/or `443` from internet

Create target group:
- Target type: `instance`
- Protocol: HTTP
- Port: `5000`
- Health check path: `/`

EC2 security group change:
- Allow `5000/tcp` **only from ALB SG** (not from 0.0.0.0/0)

Listeners:
- `80 -> target-group`
- Optional: `443 -> target-group` with ACM cert

Route53 (optional):
- Create `A/AAAA Alias` record to ALB DNS

## 7.2 Keep observability private
Recommended to not expose these publicly:
- `3000` (Grafana)
- `9090` (Prometheus)
- `16686` (Jaeger)
- `8000` (metrics)

Use one of:
- VPN / bastion / SSM Session Manager
- Private ALB + internal access
- SSH tunnel for temporary access

SSH tunnel example for Grafana:
```bash
ssh -i <key.pem> -L 3000:localhost:3000 ubuntu@<EC2_PUBLIC_IP>
```
Then open `http://localhost:3000` locally.

## 8. Security and Firewall Best Practices

- Principle of least privilege for SG rules.
- Restrict SSH to your static IP.
- Do not expose Prometheus/Grafana/Jaeger to public internet in production.
- Use HTTPS with ACM at ALB.
- Keep EC2 patched.
- Rotate credentials (`GF_SECURITY_ADMIN_PASSWORD` and Rancher bootstrap).
- Consider AWS WAF on ALB for internet-facing apps.

## 9. Kubernetes on AWS (Option C: EKS)

If you want AWS-native Kubernetes instead of Rancher-in-Docker:

High-level flow:
1. Create EKS cluster.
2. Install AWS Load Balancer Controller.
3. Build/push image to ECR.
4. Update `k8s/flask-app.yaml` image to ECR URL.
5. `kubectl apply -k k8s`.
6. Configure ingress class/annotations for AWS ALB.
7. Add monitoring stack (Prometheus/Grafana or managed Amazon Managed Prometheus/Grafana).

Notes for this repo:
- Current ingress uses `ingressClassName: nginx`; for EKS ALB ingress, update ingress spec/annotations.
- ServiceMonitor requires Prometheus Operator stack.

## 10. Useful AWS + Docker Commands

```bash
# Docker stack
docker compose up -d --build
docker compose ps
docker compose logs -f flask-app
docker compose logs -f prometheus
docker compose logs -f grafana
docker compose logs -f jaeger
docker compose down

# Instance diagnostics
sudo ss -tulpen | grep -E ':5000|:8000|:3000|:9090|:16686|:8443'
free -h
df -h
```

## 11. Troubleshooting

## App not reachable from internet
- Check EC2 SG inbound rules.
- Check NACLs if customized.
- Confirm app is listening: `docker compose ps` and `curl localhost:5000`.

## ALB target unhealthy
- Verify health check path is `/`.
- Verify EC2 SG allows `5000` from ALB SG.
- Check Flask container logs.

## Grafana/Prometheus not accessible
- Confirm SG ports and service health.
- Confirm Docker ports are mapped in `docker-compose.yml`.

## Rancher very slow/not starting
- Instance may be undersized.
- Needs privileges and enough memory/CPU.
- First startup can take several minutes.

## 12. Recommended Production Direction

For real production:
1. Put Flask app behind ALB + HTTPS.
2. Keep observability endpoints private.
3. Use ECR for images.
4. Use IaC (Terraform/CloudFormation) for VPC, SG, ALB, EC2/EKS.
5. Add backups, alerts, and centralized logs.
