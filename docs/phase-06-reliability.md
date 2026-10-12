# Phase 06 — Reliability

## Step 16: Kubernetes Probes

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
Detects whether the container is responding.
Repeated liveness failures cause Kubernetes to restart the container.

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
Step 17 — Resource Requests and Limits.
