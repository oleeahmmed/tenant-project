# Phase-1 API Standards

## Authentication

- REST APIs support:
  - `Authorization: Bearer <access_token>` (JWT)
  - Session cookie auth (dashboard browser clients)
- WebSocket chat auth uses session-authenticated user in `AuthMiddlewareStack`.

## Tenant Scope

- Every business endpoint resolves workspace tenant from request context.
- Request is rejected if:
  - no workspace tenant,
  - user is outside tenant,
  - module disabled for tenant,
  - required tenant permission missing.

## Error Contract

- API endpoints should return JSON only (`detail` and optional `errors`) and avoid HTML redirects.
- Recommended shape:
  - error: `{"ok": false, "detail": "..."}`
  - success: `{"ok": true, "data": ...}`

## Upload Contract

- Chat and Screenshot uploads use `multipart/form-data`.
- Clients should always include CSRF when using session auth in browser context.
- Mobile clients should prefer JWT auth.
