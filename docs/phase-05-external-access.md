# Phase 05 — External Access

> The NodePort and HTTP results below are historical lab verification. The current Ingress manifest uses the host `kubemart.example.com` and TLS Secret `kubemart-tls`; replace the example host and verify TLS before exposing the application.

## Step 13 — Ingress Controller

The existing NGINX Ingress Controller is managed by Helm.

- **Namespace:** `ingress-nginx`
- **IngressClass:** `nginx`
- **Controller Service:** `ingress-nginx-controller`
- **Service Type:** `NodePort`

The controller is running and has been verified as Ready.

## Step 14 — Ingress Rules

**Manifest:** `k8s/ingress/kubemart-ingress.yaml`

The `kubemart-ingress` resource is deployed in the `kubemart` namespace.

| Historical lab setting | Value |
|---|---|
| IngressClass | `nginx` |
| Host | Not specified |
| Path | `/` |
| Path type | `Prefix` |
| Backend Service | `frontend` |
| Backend Service port | `80` |

The Ingress Controller successfully recognized the resource and reloaded its NGINX configuration.

### Verification

- `kubectl describe ingress kubemart-ingress -n kubemart` showed the expected backend and three frontend endpoints.
- `curl -i http://127.0.0.1:30491/` returned `HTTP 200 OK`.
- A request using `Host: kubemart.local` also returned `HTTP 200 OK`.
- A request to `/nonexistent` returned `HTTP 404 Not Found` from the frontend NGINX server, demonstrating that Ingress routing and application-level path handling are separate.

## Step 15 — NodePort and LoadBalancer

The existing controller Service configuration:

| Setting | Value |
|---|---|
| Service type | `NodePort` |
| ClusterIP | `10.107.243.71` |
| `externalTrafficPolicy` | `Cluster` |
| HTTP Service port | `80` |
| HTTP NodePort | `30491` |
| HTTPS Service port | `443` |
| HTTPS NodePort | `31317` |

### NodePort verification

HTTP requests to the following private node addresses on port `30491` returned `HTTP 200 OK`:

- `172.31.3.158` — `k8s-master`
- `172.31.5.21` — `k8s-worker1`
- `172.31.10.26` — `k8s-worker2`

With `externalTrafficPolicy: Cluster`, traffic received by a Node can be forwarded to an appropriate Service endpoint elsewhere in the cluster.

### ClusterIP, NodePort, and LoadBalancer

- **ClusterIP:** Exposes a Service internally within the cluster.
- **NodePort:** Exposes a Service through a port on each Node's network address, subject to network access rules.
- **LoadBalancer:** Requests an external load balancer through a supported infrastructure integration. Creating this Service type does not guarantee that an external IP will be provisioned in a kubeadm cluster.

### Limitations and outstanding checks

- The tests confirmed access using private VPC addresses from the master node.
- Public internet access has not been verified.
- HTTPS connectivity and certificate validity have not been verified.
- The existing Ingress resources in the `default` namespace reference missing Services. They were left unchanged because they belong to a pre-existing setup.
- The Ingress Controller had previous restarts associated with a period when Flannel could not create a Pod sandbox. The cluster nodes and controller were Ready during the final checks.

No existing cluster resources were deleted or replaced as part of these steps.
