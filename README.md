# KubeMart — Kubernetes E-Commerce Platform

KubeMart is a hands-on Kubernetes learning project focused on building,
operating, securing, and monitoring a realistic multi-component application.

The goal is to understand Kubernetes through implementation, verification,
troubleshooting, and documentation—not just deploying manifests.

## Project Goals

- Deploy and expose application workloads using Kubernetes resources.
- Manage application configuration and sensitive credentials.
- Run stateful workloads and configure persistent storage.
- Configure Ingress, Services, and application routing.
- Practice workload reliability, scheduling, and resource management.
- Apply Kubernetes security controls and access management.
- Collect metrics and logs for monitoring and troubleshooting.
- Document implementation steps and operational lessons.

## Technology Stack

- Kubernetes v1.37.1
- Ubuntu on AWS EC2
- containerd
- Flannel CNI
- NGINX Ingress Controller
- PostgreSQL and Redis
- Helm
- Prometheus and Grafana
- Loki and Fluent Bit

## Architecture Overview

The cluster uses a control-plane node and two worker nodes.

Application traffic enters through the Ingress layer and is routed to
Kubernetes Services. The application layer includes frontend workloads,
with PostgreSQL and Redis supporting the data and caching layers.

Persistent storage is configured for the PostgreSQL workload. Monitoring
and logging components provide metrics dashboards and centralized
container-log exploration.

## Repository Structure

```text
.
├── docs/                  # Phase documentation and implementation notes
├── k8s/
│   ├── autoscaling/       # Horizontal Pod Autoscaler manifests
│   ├── config/            # Application configuration and secret templates
│   ├── deployments/       # Application deployments
│   ├── examples/          # Pod patterns and examples
│   ├── helm/              # Helm chart and values
│   ├── ingress/           # Ingress configuration
│   ├── jobs/              # Jobs and CronJobs
│   ├── monitoring/        # Monitoring and logging configuration
│   ├── namespace/         # Namespace resources
│   ├── policies/          # Reliability policies
│   ├── scheduling/        # Scheduling demonstrations
│   ├── security/          # RBAC and security examples
│   ├── services/          # Kubernetes Services
│   ├── statefulsets/      # Stateful workloads
│   ├── storage/            # StorageClass and PVC resources
│   └── workloads/         # Additional workload resources
└── README.md
```

## Prerequisites

- A reachable Kubernetes cluster with `kubectl` configured.
- Appropriate cluster permissions for the resources being deployed.
- Helm for installing or managing Helm-based components.
- A compatible storage provisioner for persistent-volume claims.
- Any required container images and configuration values.

## Working Safely with Secrets

Real credentials must not be committed to Git.

Use example files as templates, supply credentials through an appropriate
secret-management process, and verify Git's ignore rules before staging
configuration files. Kubernetes Secret manifests encoded in Base64 are
not encrypted merely because they use Base64.

## Validation

Before applying a manifest, inspect it and validate it against the target
cluster where practical:

```bash
kubectl get nodes
kubectl get namespaces
kubectl get pods -A
kubectl get services -A
kubectl get ingress -A
```

These commands inspect cluster state; they do not deploy or modify resources.

## Project Status

This repository documents an ongoing, step-by-step Kubernetes project.
Features and documentation are being reviewed before the first public
repository release. Refer to the manifests and phase documentation for
the current implementation details.

## Learning Approach

Each project step follows:

1. Understand the concept and the problem it solves.
2. Implement the Kubernetes resource.
3. Verify the result.
4. Troubleshoot relevant failure scenarios.
5. Document the implementation and lessons learned.
