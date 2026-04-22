# Phase-1 API Reference

## Auth / Tenant (`/api/auth/`)

- `POST /register/`
- `POST /verify-otp/`
- `POST /login/`
- `POST /token/refresh/`
- `POST /logout/`
- `GET|PATCH /me/`
- `GET /workspace/context/`
- `GET|PATCH /tenant/me/`
- `GET|PATCH /tenant/company-settings/`
- Role/member/invitation endpoints remain available under `/tenant/*`.

## Chat REST (`/api/chat/`)

- `GET /rooms/`
- `POST /rooms/direct/` body: `{ "user_id": number }`
- `POST /rooms/group/` body: `{ "title": "Team", "member_ids": [..] }`
- `GET /rooms/{room_id}/messages/?limit=50`
- `POST /rooms/{room_id}/messages/send/` multipart fields: `body`, `image`, `file`, `voice`

## Chat WebSocket

- URL: `/ws/chat/{room_id}/`
- Server event:
  - `{"event":"new_message","message":{...}}`
- Authorization:
  - authenticated user + room membership required.

## JiraClone (`/api/jiraclone/`)

- `GET /projects/`
- `GET /projects/{project_key}/`
- `GET /projects/{project_key}/board/`
- `GET|POST /projects/{project_key}/issues/`
- Existing board AJAX endpoints remain under `/project/{project_key}/...`

## Screenhot (`/api/screenhot/`)

- Live monitor/project/department/employee/video/screenshot/attendance endpoints available in:
  - `screenhot/api/urls.py`
- Includes:
  - `GET /live-monitor/`
  - `POST /screenshots/upload/`
  - `POST /video/generate/`
  - `GET /video/status/{job_id}/`
