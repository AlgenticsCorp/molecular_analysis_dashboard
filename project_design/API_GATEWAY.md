# API Gateway Integration Guide

This guide explains how to place a professional API Gateway (e.g., AWS API Gateway, Kong, NGINX, Azure APIM, GCP API Gateway) in front of the Molecular Analysis Dashboard API without changing core code.

## Gateway-Friendly App Settings

The API enables reverse-proxy/gateway features:
- Root path support: set `ROOT_PATH` so the app mounts under a prefix (e.g., `/api`).
- Proxy headers: honors `X-Forwarded-For` and `X-Forwarded-Proto` via ProxyHeaders middleware.
- Trusted hosts: enforce with `TRUSTED_HOSTS` (comma-separated) or `*` in dev.
- CORS: configure `CORS_ALLOW_ORIGINS` (comma-separated) or `*`.
- Request ID propagation: reads `X-Request-ID` and echoes it, or generates one.

## Required/Recommended Gateway Headers
- Forward to upstream:
  - `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host`, `X-Request-ID`
- Inject if missing:
  - `X-Request-ID`
- Optionally add:
  - `X-Forwarded-Prefix` if your gateway sets it; map it to `ROOT_PATH` env.

## Common Gateway Mappings
- Base path mapping: `/api` → upstream `http://api:8000` (Compose) or the API Service/Ingress (K8s)
- Health/ready passthrough: `/health`, `/ready`
- OpenAPI/Docs (optional public): `/openapi.json`, `/docs`

## Example: NGINX (Reverse Proxy)
```
location /api/ {
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Forwarded-Host $host;
  proxy_set_header X-Request-ID $request_id;
  proxy_pass http://api:8000/;
}
```
App env: `ROOT_PATH=/api`, `TRUSTED_HOSTS=your.domain.com`, `CORS_ALLOW_ORIGINS=https://your.domain.com`

## Example: AWS API Gateway (HTTP API)
- Integration: VPC Link → NLB → API Service
- Stage: `/api`
- Headers to pass: same as above; add mapping for request ID
- CORS: configure on gateway and/or on app via `CORS_ALLOW_ORIGINS`

## Security Notes
- JWT remains validated at the API; the gateway can add WAF/rate-limit/mTLS.
- Prefer TLS termination at gateway; re-encrypt to upstream when required.
- Use request ID and structured logs to correlate gateway ↔ upstream.

## Multi-Tenancy and Paths
- The app uses `org_id` in JWT; no path-based tenancy required.
- If you expose multiple versions, map `/v1`, `/v2` via gateway routes; set `ROOT_PATH` accordingly if mounting.

## Observability
- Propagate `X-Request-ID` to correlate across gateway and backend logs.
- Expose metrics endpoints via gateway only if intended (prefer private access).
