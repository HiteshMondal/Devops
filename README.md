# Multi-Cloud Application & Infrastructure Platform
```
            ██████╗ ███████╗██╗   ██╗ ██████╗ ██████╗ ███████╗
            ██╔══██╗██╔════╝██║   ██║██╔═══██╗██╔══██╗██╔════╝
            ██║  ██║█████╗  ██║   ██║██║   ██║██████╔╝███████╗
            ██║  ██║██╔══╝  ╚██╗ ██╔╝██║   ██║██╔═══╝ ╚════██║
            ██████╔╝███████╗ ╚████╔╝ ╚██████╔╝██║     ███████║
            ╚═════╝ ╚══════╝  ╚═══╝   ╚═════╝ ╚═╝     ╚══════╝
```

A **Production-grade Multi-Cloud Application & Infrastructure Platform project** demonstrating the full lifecycle of an application Deployment:

A multi-cloud application and infrastructure platform. One script deploys everything: containerized app, Kubernetes manifests, observability stack, and cloud infrastructure — locally or in production.

This repository provides a single-command interactive deployment runner:

```bash
./run.sh
```

---

## Architecture

```
                              ┌──────────────────────┐
                              │       run.sh         │
                              │  Deployment Runner   │
                              └──────────┬───────────┘
                                         │
                          ┌──────────────┴──────────────┐
                          │      Bootstrap Menu         │
                          │  install.sh · reset.sh ·    │
                          │  deploy workflow            │
                          └──────────────┬──────────────┘
                                         │
                              select_environment()
                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                         │
               DEPLOY_TARGET=local                    DEPLOY_TARGET=prod
        (Minikube/Kind/K3s/MicroK8s)                   (EKS/GKE/AKS/OKE)
                    │                                         │
          configure_environment()                  configure_environment()
          DEPLOY_MODE=direct                        DEPLOY_MODE=gitops
                    │                                         │
        detect_container_runtime()                select_cloud_provider()
        detect_k8s_cluster()                       select_infra_action()
                    │                               (plan / apply / destroy)
                    │                                         │
                    │                               detect_container_runtime()
                    │                                         │
                    │                          ┌──────────────┴────────────────┐
                    │                          │      deploy_infra.sh          │
                    │                          ├───────────────────────────────┤
                    │                          │ aws   → Terraform  → EKS+RDS  │
                    │                          │ azure → Pulumi     → AKS+PG   │
                    │                          │ oci   → OpenTofu   → OKE+ADB  │
                    │                          └──────────────┬────────────────┘
                    │                                         │
                    │                          detect_k8s_cluster()
                    │                          (cluster now exists post-infra)
                    │                                         │
        ┌───────────┴───────────┐                 ┌───────────┴───────────┐
        │   deploy_image()      │                 │   deploy_image()      │
        │  build_and_push_      │                 │  build_and_push_      │
        │  image.sh / _podman.sh│                 │  image.sh / _podman.sh│
        └───────────┬───────────┘                 └───────────┬───────────┘
                    │                                         │
        ┌───────────┴────────────────┐                        │
        │  DIRECT KUBERNETES PIPELINE│              ┌─────────┴───────────┐
        ├────────────────────────────┤              │   deploy_argo.sh    │
        │ deploy_kubernetes.sh       │              │  installs ArgoCD    │
        │  → Kustomize base+overlay  │              │  applies apps from  │
        │  → build/load image        │              │  generated/apps.yaml│
        │  → HPA · Ingress · Secrets │              └─────────┬───────────┘
        │                            │                        │
        │ deploy_monitoring.sh       │              Git-managed sync targets:
        │  → Prometheus              │              ┌─────────────────────────┐
        │  → Grafana                 │              │ platform/deployment/    │
        │                            │              │   kubernetes/base       │
        │ deploy_loki.sh             │              │ monitoring/prometheus   │
        │  → Loki (StatefulSet)      │              │ monitoring/loki         │
        │  → Promtail (DaemonSet)    │              │ monitoring/trivy        │
        │                            │              └─────────────────────────┘
        │ trivy.sh                   │              ArgoCD continuously
        │  → Trivy CronJob scan      │              reconciles cluster state
        │  → trivy-exporter          │              from these Git paths
        └────────────────────────────┘
                    │                                         │
                    └──────────────────┬──────────────────────┘
                                       │
                          print_access_box() — URLs, ports,
                          credentials, kubectl commands
```

---

## What's Inside

| Layer | Tooling |
|---|---|
| Application | FastAPI (Python), Uvicorn |
| Containers | Docker or Podman (auto-detected) |
| Kubernetes | Kustomize (base + local/prod overlays) |
| CI/CD | GitHub Actions, GitLab CI, ArgoCD |
| Infrastructure | Terraform (AWS), OpenTofu (OCI), Pulumi (Azure) |
| Monitoring | Prometheus, Grafana |
| Logging | Loki, Promtail |
| Security | Trivy image scanning |

Cluster distributions are auto-detected: Minikube, Kind, K3s, MicroK8s, EKS, GKE, AKS.

---

## Prerequisites

- Docker or Podman
- `kubectl`
- `helm`
- Terraform / OpenTofu / Pulumi (for the cloud you're targeting)
- AWS CLI / Azure CLI / OCI CLI (for the cloud you're targeting)
- A running Kubernetes cluster (for local mode)

Run Docker without `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## Quick Start

```bash
git clone https://github.com/HiteshMondal/devops.git
cd devops

cp .env.example .env
nano .env          # fill in required values

chmod +x run.sh
./run.sh
```

`.env` is the single source of truth for ports, variables, and secrets. `run.sh` is the single authority for local/production mode — no other script decides the environment on its own.

---

## How `run.sh` Works

```
run.sh
 │
 ├─ 1. Bootstrap menu → install deps / reset environment / deploy
 ├─ 2. Choose environment → local | production
 ├─ 3. Auto-configure services for that environment
 ├─ 4. (Production only) choose cloud provider + infra action
 ├─ 5. Confirm and run
```

### Local — Direct Deployment

Applies manifests straight to your cluster with `kubectl`.

- Build & load image
- Deploy app (Kubernetes)
- Deploy Prometheus + Grafana
- Deploy Loki + Promtail
- Deploy Trivy

### Production — GitOps

Provisions infra, then hands off to ArgoCD. Argo manages the app, monitoring, logging, and security from Git.

- Provision infrastructure (Terraform / OpenTofu / Pulumi)
- Build & push image
- Deploy ArgoCD
- ArgoCD syncs everything else from the repo

---

## Environments

### Local Clusters

| Distribution | Ingress | Service Type |
|---|---|---|
| Minikube | nginx (addon) | NodePort |
| Kind | nginx | NodePort |
| K3s | Traefik (built-in) | NodePort |
| MicroK8s | nginx (addon) | NodePort |

### Production Clouds

| Provider | IaC | Cluster | Database |
|---|---|---|---|
| AWS | Terraform | EKS | RDS PostgreSQL |
| Oracle Cloud | OpenTofu | OKE | Autonomous DB (Always-Free) |
| Azure | Pulumi | AKS | PostgreSQL Flexible Server |

---

## Project Structure

```
.
├── run.sh                     # Main orchestrator
├── .env                       # Config, ports, secrets (not committed)
├── app/                       # FastAPI application
│   └── src/
├── scripts/                   # install / reset utilities
├── platform/
│   ├── lib/                   # shared shell helpers (colors, logging)
│   ├── deployment/
│   │   ├── docker/            # image build & push
│   │   └── kubernetes/        # Kustomize base + overlays
│   ├── cicd/
│   │   ├── argo/              # ArgoCD app definitions
│   │   ├── github/
│   │   └── gitlab/
│   └── infra/
│       ├── terraform/         # AWS
│       ├── OpenTofu/          # OCI
│       └── Pulumi/            # Azure
└── monitoring/
    ├── prometheus/
    ├── grafana/
    ├── loki/
    ├── trivy/
    └── dashboards/
```
---

## Core Stack

* **Shell Scripts**: Automated shell scripts to run — [`scripts/linux_documentation.md`](./scripts/linux_documentation.md) 
* **Application**: FastAPI (Python) — [`app/app_documentation.md`](./app/app_documentation.md)
* **Containerization**: Docker / Podman — [`platform/deployment/docker/docker_documentation.md`](./platform/deployment/docker/docker_documentation.md)
* **Orchestration**: Kubernetes — [`platform/deployment/kubernetes/documentation.md`](./platform/deployment/kubernetes/documentation.md)
* **CI/CD**: GitHub Actions · GitLab CI · ArgoCD - [`platform/cicd/CICD_Documentation.md`](./platform/cicd/CICD_Documentation.md)
                                                   [`platform/cicd/github/Git_GitHub_Fundamentals.md`](./platform/cicd/github/Git_GitHub_Fundamentals.md)
* **Infrastructure**: Terraform / OpenTofu / Pulumi — [`platform/infra/documentation.md`](./platform/infra/documentation.md)
* **Monitoring**: Prometheus + Grafana + Loki — [`monitoring/documentation.md`](./monitoring/documentation.md)
* **AWS**: [`platform/infra/terraform/AWS_Documentation.md`](./platform/infra/terraform/AWS_Documentation.md)

---

## Application

FastAPI service at `app/src/main.py`, port set by `APP_PORT` in `.env`.

| Endpoint | Description |
|---|---|
| `GET /` | App info and environment |
| `GET /health` | Healthcheck (used by Kubernetes probes) |
| `GET /predict` | Model inference placeholder |
| `GET /metrics/summary` | Basic request metrics |

Built with a multi-stage Dockerfile; runs as a non-root user.

---

## Monitoring Access

```bash
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
kubectl port-forward svc/grafana 3000:3000 -n monitoring
```

Grafana Loki datasource:

```
http://loki.loki.svc.cluster.local:3100
```

Pre-built dashboards live in `monitoring/dashboards/` — import manually via **Grafana → Dashboards → Import**.

---

## Cleanup

```bash
./scripts/reset.sh
```

Runs a selective, destructive cleanup of containers, cluster resources, and local state.

---

## Documentation

Each component has its own doc alongside its code:

- `scripts/linux_documentation.md`
- `platform/deployment/docker/docker_documentation.md`
- `platform/deployment/kubernetes/documentation.md`
- `platform/cicd/CICD_Documentation.md`
- `platform/cicd/github/Git_GitHub_Fundamentals.md`
- `platform/infra/documentation.md`
- `platform/infra/terraform/AWS_Documentation.md`
- `monitoring/documentation.md`

---

## Author

**Hitesh Mondal** — DevOps · Cloud · Cybersecurity

## License

Open for learning and demonstration purposes.