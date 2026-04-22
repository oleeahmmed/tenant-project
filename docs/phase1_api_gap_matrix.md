# Phase-1 API Gap Matrix

This matrix maps current web features to API readiness for external Android/React clients.

## TenantAuth

| Feature | Web | API Status | Notes |
|---|---|---|---|
| Register/OTP/Login/Refresh | Yes | Ready | In `auth_tenants/api` |
| Me/Profile details | Yes | Partial | `me/` exists, profile update endpoint missing |
| Workspace tenant context | Yes | Partial | `tenant/me` exists, explicit context/snapshot endpoint missing |
| Company settings | Yes | Missing | New API endpoint needed |
| Permission snapshot | Yes | Missing | Needed for client feature-gating |

## Chat

| Feature | Web | API Status | Notes |
|---|---|---|---|
| Room list/select | Yes | Missing | Template-only currently |
| Direct/group room create | Yes | Missing | `chat/services.py` exists but no REST endpoints |
| Message list/pagination | Yes | Missing | Template-only currently |
| Send text/image/file/voice | Yes | Missing | Template POST view exists |
| WebSocket receive | Yes | Ready | `ws/chat/<room_id>/` exists |

## JiraClone

| Feature | Web | API Status | Notes |
|---|---|---|---|
| Board issue actions | Yes | Partial | Existing AJAX endpoints in `jiraclone/api` |
| Project list/detail for clients | Yes | Missing | Need read APIs for project browsing |
| Board payload endpoint | Yes | Missing | Need statuses + issue columns in one payload |
| Issue list/create (external clients) | Yes | Partial | Quick-create exists; general list/create missing |
| Comments/assignment/status | Yes | Ready/Partial | Exists but needs JSON-only conventions for external clients |

## Screenhot

| Feature | Web | API Status | Notes |
|---|---|---|---|
| Live monitor (project/department) | Yes | Ready | Implemented in `screenhot/api` |
| Screenshot list/upload/delete | Yes | Ready | Implemented |
| Attendance flow | Yes | Ready | Implemented |
| Video generation/status/list/delete | Yes | Ready | Implemented |

## Cross-cutting Gaps

- JSON-only permission/auth failures needed (no HTML redirect semantics for API clients)
- Consistent error contract and envelope needed across legacy AJAX and DRF endpoints
- API docs for external client onboarding needed
