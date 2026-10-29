# ☸️ KubeMart — Kubernetes E-Commerce Platform

<p align="center">
  <strong>A hands-on Kubernetes platform focused on cloud-native deployment, reliability, security, and observability.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Kubernetes-Platform-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes">
  <img src="https://img.shields.io/badge/Container%20Runtime-containerd-575757" alt="containerd">
  <img src="https://img.shields.io/badge/Networking-Flannel-00AEEF" alt="Flannel">
  <img src="https://img.shields.io/badge/Monitoring-Prometheus-E6522C?logo=prometheus&logoColor=white" alt="Prometheus">
  <img src="https://img.shields.io/badge/Dashboards-Grafana-F46800?logo=grafana&logoColor=white" alt="Grafana">
  <img src="https://img.shields.io/badge/Logging-Loki-7B61FF" alt="Loki">
</p>

---

## 📖 Overview

**KubeMart** is a Kubernetes learning and engineering project built to explore how cloud-native workloads are deployed, exposed, secured, scheduled, monitored, and maintained.

The repository brings together Kubernetes manifests, Helm configuration, operational scripts, and technical documentation. Its focus is on understanding Kubernetes concepts through practical implementation rather than relying only on theoretical examples.

### Project goals

- Deploy and manage application workloads using Kubernetes.
- Expose applications through Services and Ingress.
- Configure application settings and sensitive configuration separately.
- Explore persistent storage for stateful workloads.
- Practice health, availability, scheduling, and autoscaling concepts.
- Apply Kubernetes security controls and access management.
- Build an observability stack for metrics, dashboards, and logs.
- Document implementation decisions, verification steps, and troubleshooting.

> **Project status:** This repository contains implementation manifests and learning labs. The presence of a manifest does not, by itself, prove that the resource is currently deployed or production-ready.

## Arabic learning guide

- [Read the 19-page Arabic DevOps guide](output/pdf/KubeMart-DevOps-Guide-Arabic.pdf)
- [View the editable HTML source](output/pdf/KubeMart-DevOps-Guide-Arabic.html)
- [View the English architecture diagram (SVG)](output/pdf/KubeMart-Architecture.svg)

On Windows, regenerate the PDF and SVG from the HTML source with `./output/pdf/generate.ps1` after installing Chrome or Edge. The ECR account value in the guide is a placeholder; replace it with an account you control before running those commands.

---

## 🏗️ Architecture

The following is a **logical architecture overview** based on the components represented in this repository. It describes intended component relationships, not a live inventory of deployed resources.

### 1. Application Architecture

This diagram shows the application request path represented by the manifests and code.

```mermaid
flowchart TB
    USER["Users / Clients"]

    subgraph ACCESS["Application Access"]
        ING["NGINX Ingress Controller"]
        RULE["KubeMart Ingress"]
        SVC["Frontend Service :80"]
        FE["Frontend NGINX :8080"]
        API_SVC["KubeMart API Service :8000"]
        API["FastAPI backend"]
    end

    subgraph DATA["Data Services"]
        REDIS_SVC["Redis Service :6379"]
        REDIS["Redis Deployment"]
        PG_SVC["PostgreSQL Headless Service :5432"]
        PG["PostgreSQL StatefulSet"]
        PVC["PersistentVolumeClaim"]
        SC["StorageClass"]
    end

    USER --> ING
    RULE -. "Configures routing rules" .-> ING
    ING --> SVC
    SVC --> FE
    FE -->|"Proxies /api"| API_SVC
    API_SVC --> API
    API -->|"Credentials from Kubernetes Secret"| PG_SVC
    REDIS_SVC --> REDIS
    API -. "Separate lab workload; not used by app code" .-> REDIS_SVC
    PG_SVC --> PG
    PG --> PVC
    SC -. "Storage provisioning parameters" .-> PVC
```

### 2. Platform Operations

This diagram separates operational controls from application traffic. Dashed lines represent configuration or policy relationships, not direct network traffic.

```mermaid
flowchart TB
    subgraph OBS["Observability"]
        PROM["Prometheus<br/>Metrics collection"]
        GRAF["Grafana<br/>Dashboards and queries"]
        FB["Fluent Bit<br/>Log collection"]
        LOKI["Loki<br/>Log storage and queries"]

        GRAF -->|"Queries metrics"| PROM
        GRAF -->|"Log queries"| LOKI
        FB -->|"Ships logs"| LOKI
    end

    subgraph REL["Reliability and Scheduling"]
        HPA["Horizontal Pod Autoscaler"]
        PDB["PodDisruptionBudget"]
        JOB["Jobs and CronJobs"]
        SCHED["Node Selector / Affinity / Taints"]
    end

    subgraph SEC["Security and Resource Governance"]
        RBAC["Roles and RoleBindings"]
        NP["NetworkPolicy"]
        QUOTA["ResourceQuota"]
        CTX["Security Context"]
    end

    APP["KubeMart Workloads"]

    HPA -. "Scaling policy" .-> APP
    PDB -. "Disruption policy" .-> APP
    SCHED -. "Placement constraints" .-> APP
    RBAC -. "Authorization rules" .-> APP
    NP -. "Traffic policy" .-> APP
    QUOTA -. "Resource constraints" .-> APP
    CTX -. "Container security settings" .-> APP
```

### Architecture notes

- **Ingress and Services:** provide the configuration path for routing external application traffic to Kubernetes workloads.
- **Frontend and API:** the custom NGINX image serves the storefront and proxies `/api/` to FastAPI. Order creation requires a signed-in customer account.
- **PostgreSQL:** represented by a StatefulSet, Service, and persistent-storage configuration.
- **Redis:** represented by a separate lab Deployment and Service; the KubeMart application code does not use it.
- **Reliability:** includes HPA and PodDisruptionBudget manifests, along with workload scheduling examples.
- **Security:** includes RBAC, NetworkPolicy, ResourceQuota, and security-context examples.
- **Observability:** includes configuration for Prometheus, Grafana, Loki, and Fluent Bit.

Dashed connections indicate policies, configuration relationships, or application dependencies that must be verified against the deployed configuration. They do not establish that every connection is currently active.

### Application authentication

Customers create an account with a name, email address, and password of at least 12 characters, or sign in with an existing account. The API validates email addresses, stores Argon2 password hashes, and issues a random session token in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie. PostgreSQL stores only a hash of each session token. Sessions expire after seven days and are revoked on sign-out. Order creation requires a valid session and uses the signed-in account's name and email rather than accepting identity fields in the order request.

The `kubemart-reader` ServiceAccount and RBAC examples control access to the Kubernetes API. They are separate from KubeMart customer accounts. The app does not yet include password reset or email verification; those are required before using customer accounts for a real commerce service.

The Kubernetes API deployment marks the session cookie Secure. Use HTTPS for the configured host. For local HTTP-only development, set `SESSION_COOKIE_SECURE=false` in the local backend environment only; never use that setting for an internet-facing deployment.

### Edit the architecture diagram

The diagram above is written in Mermaid. To change it:

1. Open `README.md`.
2. Find the section starting with ` ```mermaid `.
3. Edit the nodes and connections inside that block.
4. Save and push the changes to GitHub.
5. Open the repository README to see the rendered diagram.

You can also copy the Mermaid block into the [Mermaid Live Editor](https://mermaid.live/) to preview changes before committing them.

---

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Kubernetes | Workload orchestration and cluster resource management |
| containerd | Container runtime |
| Flannel | Cluster pod networking |
| Kubernetes Services | Stable internal service discovery and access |
| Ingress | HTTP/HTTPS routing configuration |
| PostgreSQL | Relational database workload |
| Redis | In-memory data-store workload |
| PersistentVolumeClaim / StorageClass | Persistent-storage configuration |
| Helm | Packaging and configuration of supported components |
| Prometheus | Metrics collection and monitoring |
| Grafana | Dashboards and visualization |
| Loki | Log aggregation |
| Fluent Bit | Log collection and forwarding |

The exact deployed versions and enabled features should be verified against the running cluster and Helm releases.

---

## 📂 Repository Structure

```text
KubeMart/
├── app/
│   ├── backend/
│   └── frontend/
├── .github/
│   └── workflows/
├── docs/
│   ├── phase-05-external-access.md
│   ├── phase-06-reliability.md
│   ├── phase-07-workloads.md
│   ├── phase-09-security-rbac.md
│   └── phase-10-application-authentication.md
├── k8s/
│   ├── autoscaling/
│   ├── config/
│   ├── deployments/
│   ├── examples/
│   ├── helm/
│   ├── ingress/
│   ├── jobs/
│   ├── monitoring/
│   ├── namespace/
│   ├── policies/
│   ├── scheduling/
│   ├── security/
│   ├── services/
│   ├── statefulsets/
│   ├── storage/
│   └── workloads/
├── .gitignore
└── README.md
```

Directory contents may evolve as the project progresses.

---

## ☸️ Kubernetes Topics Covered

### Workloads and application access

- Deployments and Pods
- Services and service discovery
- Ingress routing
- StatefulSets
- Jobs and CronJobs
- Init containers and sidecar examples

### Reliability and scaling

- Horizontal Pod Autoscaler configuration
- PodDisruptionBudget
- Workload health and availability concepts
- Resource management and scheduling constraints

### Scheduling

- Node selectors
- Affinity and anti-affinity concepts
- Taints and tolerations

### Security

- ServiceAccounts and RBAC-related resources
- Role and RoleBinding examples
- NetworkPolicy examples
- Security contexts
- ResourceQuota
- Separation of sensitive configuration from application manifests

### Storage

- StorageClass configuration
- PersistentVolumeClaim
- Stateful workload storage
- PostgreSQL storage verification examples

### Observability

- Prometheus configuration
- Grafana configuration
- Loki configuration
- Fluent Bit configuration

---

## 🚀 Getting Started

### Prerequisites

A working Kubernetes environment is required for cluster operations.

Recommended tools:

- `kubectl`
- Helm
- Git
- Access to a Kubernetes cluster and the required permissions

The exact cluster setup depends on your environment.

### 1. Clone the repository

```bash
git clone https://github.com/mhmdhmdbdh2050/kubemart-kubernetes-platform.git
cd kubemart-kubernetes-platform
```

If you already have the project locally, navigate to its directory instead.

### 2. Inspect the cluster

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get namespaces
```

Confirm that the cluster is reachable and the nodes are in a healthy state before applying workloads.

### 3. Review the manifests

```bash
find app k8s docs -maxdepth 4 -type f | sort
```

Inspect the namespace, application configuration, Services, storage, Ingress, and monitoring manifests before deployment.

### 4. Configure database, registry, and TLS credentials

```bash
cat k8s/config/postgres-secret.example.yaml
```

Copy the PostgreSQL example to `k8s/config/postgres-secret.yaml` and replace the placeholders locally. After creating the `kubemart` namespace, apply this file there. The real file is ignored by Git. The frontend does not receive database credentials. Both application Deployments reference `ecr-pull-secret`; provision it in the namespace using your approved registry credential process before deploying the private ECR images.

Build and push the backend and frontend images to the ECR repositories configured in the manifests. Use a new tag for each build. The Ingress uses the example host `kubemart.example.com` and expects a TLS Secret named `kubemart-tls`; replace the host with one you control and create the TLS Secret from its certificate and private key in the `kubemart` namespace before applying the Ingress.

```bash
REGISTRY=771962256401.dkr.ecr.us-east-1.amazonaws.com
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$REGISTRY"
docker build -f app/backend/Dockerfile -t "$REGISTRY/kubemart-api:v3" app/backend
docker push "$REGISTRY/kubemart-api:v3"
docker build -f app/frontend/Dockerfile -t "$REGISTRY/kubemart-frontend:v1" app/frontend
docker push "$REGISTRY/kubemart-frontend:v1"
```

Create the TLS Secret with your certificate and private key, for example:

```bash
kubectl create secret tls kubemart-tls --namespace kubemart \
  --cert=/path/to/fullchain.pem --key=/path/to/private-key.pem
```

**Never paste real passwords, tokens, or private credentials into this README or a public Git repository.**

### 5. Deploy and verify resources

Apply manifests in dependency order. The ECR pull Secret and TLS Secret must exist first.

```bash
kubectl apply -f k8s/namespace/namespace.yaml
kubectl apply -f k8s/config/postgres-secret.yaml
kubectl apply -f k8s/storage/kubemart-storageclass.yaml
kubectl apply -f k8s/storage/postgres-pvc.yaml
kubectl apply -f k8s/services/postgres-service.yaml
kubectl apply -f k8s/statefulsets/postgres-statefulset.yaml
kubectl rollout status statefulset/postgres -n kubemart
kubectl apply -f k8s/app/backend.yaml
kubectl apply -f k8s/deployments/frontend-deployment.yaml
kubectl apply -f k8s/services/frontend-service.yaml
kubectl apply -f k8s/security/network-policy-example.yaml
kubectl apply -f k8s/security/api-ingress-policy.yaml
kubectl apply -f k8s/security/postgres-ingress-policy.yaml
kubectl apply -f k8s/ingress/kubemart-ingress.yaml
```

StorageClass settings may need adjustment for the cluster. Standalone examples and lab resources under `k8s/examples/` and `k8s/helm/` are not part of this application deployment sequence.

The following commands are for inspection; they do not create or modify resources.

```bash
kubectl get all -A
kubectl get ingress -A
kubectl get pvc -A
kubectl get hpa -A
kubectl get pods -A
```

Use the results to establish which resources are actually deployed. Apply manifests only after reviewing their dependencies, namespace settings, storage requirements, and configuration.

Confirm the cluster has the expected storage provisioner, ingress controller, DNS, registry access, and NetworkPolicy enforcement before deployment. The CI workflow compiles backend source, builds both images, and validates Kubernetes manifests (excluding Helm values); it does not deploy to a cluster.

---

## 📊 Monitoring and Logging

The repository contains configuration files for:

- **Prometheus:** metrics collection and monitoring configuration.
- **Grafana:** dashboard and data-source configuration.
- **Loki:** log aggregation configuration.
- **Fluent Bit:** log collection and forwarding configuration.

Useful inspection commands:

```bash
helm list -A
kubectl get pods -A
kubectl get services -A
kubectl get configmaps -A
```

A configuration file existing in the repository does not guarantee that its Helm release is installed, its Pods are healthy, or its dashboards and data sources are working. Verify each component independently.

---

## 🔐 Security Considerations

- API order creation requires a customer account. Passwords are hashed with Argon2 and session cookies are `HttpOnly`, `Secure`, and `SameSite=Strict`.
- Configure the Ingress host and TLS certificate together, and verify HTTPS before handling customer data.
- Keep database credentials out of frontend Pods. Only the API and PostgreSQL workloads need the database Secret.
- API and PostgreSQL NetworkPolicies restrict inbound traffic to the application components; confirm the cluster CNI enforces NetworkPolicy.
- Never commit real credentials or unredacted Secret manifests.
- Use example files for documentation and safe configuration templates.
- Review `.gitignore` before staging configuration files.
- Apply least-privilege RBAC permissions.
- Restrict network traffic where suitable NetworkPolicies are supported.
- Use appropriate container security contexts.
- Define resource requests and limits according to workload requirements.
- Review Kubernetes and Helm changes before applying them to a cluster.
- Rotate any credential that may have been exposed.

Kubernetes Secrets provide an API mechanism for handling sensitive values; they should not automatically be treated as encrypted or safe merely because they are stored in a Secret object. Configure appropriate access controls and encryption at rest for the cluster.

---

## 🧪 Troubleshooting

Start with cluster and workload status:

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get events -A --sort-by=.metadata.creationTimestamp
```

Inspect a particular Pod:

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
```

Inspect application routing and storage:

```bash
kubectl get ingress,services -A
kubectl get pvc -A
kubectl get endpointslices -A
```

Replace placeholders such as `<pod-name>` and `<namespace>` with the actual values from your cluster.

For a production incident, correlate Pod events, application logs, Service selectors, EndpointSlices, readiness probes, network policies, and resource constraints before changing the configuration.

---

## 🗺️ Roadmap

The project can continue to evolve through the following areas:

- Complete and validate the observability dashboards.
- Improve security policies and least-privilege access.
- Verify autoscaling behavior under representative load.
- Expand automated validation and operational scripts.
- Improve deployment reproducibility and configuration management.
- Document recovery procedures and operational runbooks.
- Add repeatable testing for application availability and dependencies.

These are development goals, not claims that every item is already implemented.

---

## 📚 Documentation

Implementation notes are maintained in the `docs/` directory. Start with the phase documents to understand the project's external-access, reliability, and workload exercises.

See [Phase 10 — Application Authentication](docs/phase-10-application-authentication.md) for account, session, cookie, and order-access behavior.

For practical learning, follow this cycle:

**Understand → Implement → Verify → Troubleshoot → Document**

---

## 👨‍💻 Author

**Mohamed Ahmed Abdo**

DevOps and Cloud Engineering | Kubernetes | Linux | Docker | AWS

GitHub: [@mhmdhmdbdh2050](https://github.com/mhmdhmdbdh2050)

Project repository: [KubeMart Kubernetes Platform](https://github.com/mhmdhmdbdh2050/kubemart-kubernetes-platform)

---
