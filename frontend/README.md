# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Backend API integration

This frontend uses a small fetch-based API client at `src/api` and expects a backend API base URL in the environment variable `VITE_API_BASE_URL`.

- Default (if not set): `http://localhost:8000/api/v1`
- Set `VITE_API_BASE_URL` to point to your backend when running locally or in CI.

Health & debug endpoints

The backend exposes simple health endpoints used by the development UI:

- GET `${VITE_API_BASE_URL}/health` — returns `{status: "ok"}` when healthy.
- GET `${VITE_API_BASE_URL}/debug-test` — returns a debug payload (useful for development).
- GET `${VITE_API_BASE_URL}/chat` — placeholder chat status endpoint (returns router status).

The app shows a small `ApiStatus` panel in development mode (bottom-right) that polls these endpoints every 10s. To test manually from PowerShell:

```powershell
# From repository root, start the backend (example using uvicorn if FastAPI is the backend):
# uvicorn backend.app.main:app --reload --port 8000

cd frontend
npm install
npm run dev

# Quick curl-like tests (PowerShell):
(Invoke-WebRequest -UseBasicParsing "http://localhost:8000/api/v1/health").Content | ConvertFrom-Json
(Invoke-WebRequest -UseBasicParsing "http://localhost:8000/api/v1/debug-test").Content | ConvertFrom-Json
(Invoke-WebRequest -UseBasicParsing "http://localhost:8000/api/v1/chat").Content | ConvertFrom-Json
```

If your backend runs on a different origin, set the Vite env var before starting the dev server (PowerShell):

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000/api/v1'; npm run dev
```

Notes

- The `ApiStatus` component is only rendered in development (`import.meta.env.DEV`) to avoid exposing debug UI in production.
- Authentication endpoints are not implemented in the backend yet; the frontend has a placeholder `auth.status()` helper that calls `/auth`.

## WebSocket (streaming chat) integration

The backend provides a WebSocket endpoint for real-time/streaming chat at `/api/v1/chat/ws/message`.

- Set `VITE_WS_BASE_URL` to the WebSocket origin (example: `ws://localhost:8000` or `wss://your-domain.com`). The frontend will connect to `${VITE_WS_BASE_URL}/api/v1/chat/ws/message`.

Quick test using `wscat` (npm package):

```powershell
# install wscat globally if you don't have it
npm i -g wscat

# connect
wscat -c ws://localhost:8000/api/v1/chat/ws/message

# then send JSON messages like:
# {"message":"Hello","thread_id":null}
```

Browser console test (paste in DevTools console):

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws/message');
ws.onopen = () => ws.send(JSON.stringify({ message: 'Hi there', thread_id: null }));
ws.onmessage = (ev) => console.log('msg', JSON.parse(ev.data));
```

If WS fails, the frontend will fallback to the existing HTTP POST `/api/v1/message` endpoint.


