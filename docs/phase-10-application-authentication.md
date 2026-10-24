# Phase 10 — Application Authentication

## Scope

This phase covers customer authentication for the KubeMart HTTP API. It is separate from Kubernetes ServiceAccount authentication and RBAC, which control access to the Kubernetes API.

## Account flow

1. A customer submits a name, email address, and password to `POST /api/auth/register`, or email and password to `POST /api/auth/login`.
2. The API validates the email address and password length, hashes new passwords with Argon2, and stores account records in PostgreSQL.
3. After registration or sign-in, the API generates a random session token. It stores only the SHA-256 digest of the token in the `sessions` table and returns the token in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie.
4. Authenticated requests are checked against an unexpired session record. `POST /api/auth/logout` deletes the current session and clears the cookie.
5. `POST /api/orders` requires an active session. Customer name and email are taken from the account record, not from client-submitted order data.

Sessions expire after seven days. Expired records are removed when a new session is issued. Passwords must be at least 12 characters; password reset and email verification are not implemented.

## Transport and local development

The cookie is Secure by default and the Kubernetes Deployment explicitly sets `SESSION_COOKIE_SECURE=true`. The Ingress host must be a domain controlled by the operator, and a TLS Secret named `kubemart-tls` must be created for it. Do not disable cookie Secure on a public deployment.

For local HTTP development only, set `SESSION_COOKIE_SECURE=false` in the backend environment. SameSite cookie policy and the API's Origin check remain enabled.

## Database migration

The API creates `users` and `sessions` tables at startup and adds a nullable `user_id` column to existing `orders` tables. Existing orders are preserved without an account association; new orders reference the signed-in user. Back up the database before deploying application changes to a non-disposable environment.

## Verification checklist

- Register a new account and confirm the response sets a Secure, HttpOnly, SameSite=Strict session cookie.
- Confirm the database stores a password hash and a digest of the session token, not the raw values.
- Confirm `GET /api/auth/me` returns the current account and rejects requests without a valid session.
- Confirm logout revokes the session and clears the browser cookie.
- Confirm `POST /api/orders` rejects an unauthenticated request and uses account name/email for an authenticated request.
- Confirm a cross-origin request with a mismatched Origin is rejected.
- Confirm existing orders remain available after the schema migration and are not assigned to an arbitrary account.
