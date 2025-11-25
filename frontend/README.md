## CG RERA Explorer – Frontend

Minimal React + Vite UI to browse CG RERA projects from the Phase 6 backend.

### Prerequisites
- Node 18+
- Backend API running locally (default `http://localhost:8000`)

### Setup
1) `cd frontend`
2) Copy env and adjust if needed:
```bash
cp .env.example .env
# edit VITE_API_BASE_URL if your backend runs elsewhere
```
3) Install deps:
```bash
npm install
```

### Development
Run the dev server (defaults to http://localhost:5173):
```bash
npm run dev
```
Make sure the backend API is reachable at `VITE_API_BASE_URL` (e.g., start FastAPI with `uvicorn cg_rera_extractor.api.app:app --reload --port 8000` from the repo root).

### Build
```bash
npm run build
npm run preview
```

### Tests
Lightweight unit/component checks:
```bash
npm test
```

### Notes
- Map uses OpenStreetMap tiles via `react-leaflet`.
- API calls use a single axios client configured by `VITE_API_BASE_URL`.
- Basic filters: district dropdown, min overall score slider, name substring search.
