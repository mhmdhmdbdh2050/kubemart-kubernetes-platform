# Phase 06 — Reliability

## Historical lab record — Step 16: Kubernetes Probes

The values below describe the frontend Deployment at the time of the original
lab verification. The current custom frontend listens on port `8080`; its
current probes use the named `http` port. See
`k8s/deployments/frontend-deployment.yaml` for the active configuration.

### Objective
Configure and verify readiness and liveness probes
for the KubeMart frontend Deployment.

### Readiness Probe
- Type: HTTP GET
- Path: /
- Port: 80
- Initial delay: 5 seconds
- Period: 5 seconds
- Timeout: 2 seconds
- Failure threshold: 3

Purpose:
Determines whether the container is ready to receive traffic.
A failed readiness probe removes the Pod from ready Service endpoints.
It does not restart the container by itself.

### Liveness Probe
- Type: HTTP GET
- Path: /
- Port: 80
- Initial delay: 15 seconds
- Period: 10 seconds
- Timeout: 2 seconds
- Failure threshold: 3

Purpose:
Detects whether the frontend NGINX container is responding.
Repeated liveness failures cause Kubernetes to restart the container.

### Current KubeMart API probes

The API Deployment uses `/health` for readiness, which checks PostgreSQL connectivity, and `/live` for liveness, which checks only the API process. Keeping dependency checks out of the liveness probe avoids restarting healthy API processes during a database interruption.

### Verification
- Manifest validation:
  `kubectl apply --dry-run=client -f k8s/deployments/frontend-deployment.yaml`
- Result: `deployment.apps/frontend unchanged (dry run)`
- All three frontend Pods were Running and Ready.
- Ingress NodePort test returned HTTP 200.
- PostgreSQL returned `accepting connections`.

### Restart Investigation
The frontend containers previously restarted with exit code 255.
Cluster events showed EC2 node reboots and temporary Flannel
network initialization failures.
These events suggest infrastructure disruption as a likely cause.
The exact cause of each container restart was not conclusively established.

### Notes
Readiness and liveness probes serve different purposes.
A successful HTTP response on `/` confirms basic NGINX responsiveness,
not the health of every application function.

### Next Step
## Step 18 — Rolling Updates and Rollbacks

### Rolling Update
- Updated the frontend image from `nginx:1.27` to `nginx:1.28` using `kubectl set image`.
- Kubernetes created a new ReplicaSet and replaced frontend Pods gradually.
- The rollout completed successfully with 3/3 replicas ready.
- Verified the frontend Service returned HTTP 200 OK and reported `nginx/1.28.3`.

### Rollback
- Compared Revision 9 and Revision 10 before rollback.
- Confirmed both revisions retained the same resource requests, limits, readiness probe, liveness probe, ConfigMap reference, and Secret reference.
- Rolled back to Revision 9 using `kubectl rollout undo`.
- The rollback completed successfully and the Deployment returned to `nginx:1.27` with 3/3 replicas ready.

### Key Lessons
- A Deployment revision records changes to the Pod template.
- RollingUpdate gradually replaces Pods according to `maxSurge` and `maxUnavailable`.
- `kubectl rollout undo` restores a previous Pod template and creates a new rollout.
- The Git manifest should remain the source of truth; keep it aligned with the intended Deployment configuration.
- A successful rollout confirms deployment progress, while application-level checks provide additional evidence of service health.
## Step 19 — Horizontal Pod Autoscaler (HPA)

### Metrics Server
- Installed Metrics Server v0.9.0 to provide resource metrics.
- Initial scraping failed because kubelet certificates did not contain the node IP addresses as IP SANs.
- For this lab, added `--kubelet-insecure-tls` to the Metrics Server Deployment.
- Metrics Server became ready, and `kubectl top nodes` returned CPU and memory metrics.
- Security note: insecure kubelet TLS is a lab-only workaround. Production environments should use properly configured kubelet certificates.

### Frontend HPA
- Created `k8s/autoscaling/frontend-hpa.yaml`.
- Target: Deployment `frontend` in namespace `kubemart`.
- Metric: CPU utilization, target 60% of requested CPU.
- Minimum replicas: 3.
- Maximum replicas: 6.
- Verified `ScalingActive=True` and `ValidMetricFound`.
- At verification time, CPU utilization was 2% and the Deployment remained at 3 replicas.

### Key Lessons
- HPA adjusts replica count using resource metrics and target utilization.
- CPU utilization is calculated relative to CPU requests, not CPU limits.
- A low CPU utilization does not trigger scale-up.
- Metrics Server supplies metrics; the HPA controller uses those metrics to make scaling decisions.
## Step 20 — PodDisruptionBudget (PDB)

- Created `k8s/policies/frontend-pdb.yaml`.
- Namespace: `kubemart`.
- Selector: `app=frontend`.
- `minAvailable: 2` ensures at least two frontend Pods remain available during supported voluntary disruptions.
- Verified the PDB reports 3 current Pods, 3 total Pods, and 1 allowed disruption.
- No drain operation was performed.

### Key Lessons
- A PDB helps protect availability during supported voluntary disruptions.
- PDBs do not guarantee availability during involuntary failures, such as an unexpected node crash.
- PDBs do not replace readiness probes, replicas, or rolling update settings.
Step 17 — Resource Requests and Limits.
