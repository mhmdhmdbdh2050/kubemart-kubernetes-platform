# Phase 09 — Security: ServiceAccounts & RBAC

## Objective
Practice Kubernetes RBAC using a dedicated ServiceAccount with least-privilege permissions.

## Resources
- ServiceAccount: `kubemart/kubemart-reader`
- ClusterRole: `namespace-reader`
- ClusterRoleBinding: `namespace-reader-binding`
- Role: `kubemart/pod-reader`
- RoleBinding: `pod-reader-binding`

## Permissions

### Cluster-scoped
The `namespace-reader` ClusterRole grants `get`, `list`, and `watch` on core API resource `namespaces`.

### Namespace-scoped
The `pod-reader` Role grants `get`, `list`, and `watch` on core API resource `pods` within the `kubemart` namespace.

## Verification Results

| Operation | Result |
|---|---|
| List namespaces | `yes` |
| Delete namespaces | `no` |
| List Pods in `kubemart` | `yes` |
| Delete Pods in `kubemart` | `no` |

## In-Pod Verification

A temporary Pod named `rbac-test` was created in the `kubemart` namespace
using the `kubemart-reader` ServiceAccount and with ServiceAccount token
automounting enabled.

| Test from inside `rbac-test` | Result |
|---|---|
| `kubectl get pods -n kubemart` | Succeeded |
| `kubectl auth can-i delete pods -n kubemart` | `no` |

The temporary test Pod was deleted after verification. Its resource requests
and limits were specified to satisfy the `kubemart-quota` ResourceQuota.

## Key Lessons
- A Role grants permissions within one namespace.
- A ClusterRole can grant permissions to cluster-scoped resources.
- A RoleBinding associates permissions with subjects in its namespace.
- A ClusterRoleBinding grants cluster-scoped permissions from a ClusterRole.
- Permissions from multiple bindings are additive; Kubernetes RBAC has no explicit deny rules.
- `kubectl auth can-i` tests effective authorization without modifying resources.

These results describe the permissions observed during this lab and are not a complete audit of all effective permissions.
