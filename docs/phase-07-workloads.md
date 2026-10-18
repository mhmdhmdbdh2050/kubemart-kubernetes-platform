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
## Step 22 — Sidecar Container

- Created `k8s/examples/sidecar-pod.yaml`.
- Ran NGINX and a log-reader sidecar in the same Pod.
- Shared NGINX logs through an `emptyDir` volume.
- Mounted the shared volume read-only in the sidecar.
- Used `tail -F` to stream the NGINX access log to the sidecar's standard output.
- Generated an HTTP request from the sidecar to `127.0.0.1`.
- Verified `HTTP/1.1 200 OK` and an access log entry containing `GET / HTTP/1.1` with status `200`.

### Key Lessons
- Containers in the same Pod share the Pod network namespace and can communicate through `localhost`.
- Containers can share files through a common volume.
- A sidecar can process or forward application logs without being part of the main application container.
- `emptyDir` is temporary storage and does not persist after the Pod is removed.
-Step 23 — Kubernetes Job

Objective: Run a finite, one-time workload and verify that it completes successfully.

Manifest: "k8s/jobs/completion-report-job.yaml"

Configuration:

- "completions: 1" — require one successful completion.
- "parallelism: 1" — run at most one Job Pod at a time.
- "backoffLimit: 2" — allow up to two retries after failed attempts, subject to other Job limits.
- "activeDeadlineSeconds: 120" — limit the Job's active execution time.
- "restartPolicy: Never" — do not restart the container within the same Pod after it exits.

Execution: The BusyBox container simulates a completion report by processing sample order IDs "101", "102", and "103".

Verification results:

- Job status: "Complete"
- Completions: "1/1"
- Duration: "12s"
- Pod status: "Completed"
- Restarts: "0"
- Logs confirmed "Report completed successfully."

Key takeaway: A Kubernetes Job manages Pods that execute finite tasks and tracks whether the required number of successful completions has been reached. A CronJob can create Jobs automatically on a schedule.

Limitation: This is a simulated report; it does not process real orders or connect to the KubeMart database.
