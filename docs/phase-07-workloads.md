# Phase 07 — Workloads

## Step 21 — Init Container

- Created `k8s/examples/init-container-pod.yaml`.
- Added an init container named `wait-for-frontend` using `busybox:1.36`.
- The init container retries an HTTP request to `http://frontend:80/` every three seconds until the request succeeds.
- The NGINX application container starts only after the init container completes successfully.
- Verified `frontend-init-demo` reached `Running`, with `1/1` containers ready and zero restarts.

### Key Lessons
- Init containers run to completion before application containers start.
- A failed init container prevents the application containers from starting.
- Init containers are useful for setup tasks and dependency checks, but they do not replace application readiness probes.
- This is an isolated demonstration Pod, not a change to the production-style frontend Deployment.
-
