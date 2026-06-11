# RegRadar — Landing Page

B2B SaaS landing page for RegRadar: AI-powered regulatory monitoring for undercovered markets.

## Stack

- React + Vite
- Tailwind CSS v4 (`@tailwindcss/vite`)
- Recharts (risk trend chart)
- TanStack Table (source health table)
- lucide-react (icons)
- Mock data only — no backend calls

## How to run locally

```bash
cd web
npm install
npm run dev
```

Open: http://localhost:5173

## How to build

```bash
npm run build
```

Output is in `web/dist/` — ready for static hosting (Vercel, Netlify, GitHub Pages).

## Notes

- Frontend is currently mock-data only (`src/data/mockData.js`)
- Backend integration will be added in a later phase
- No API keys are required for the frontend
- Do not modify Python backend files (`app/`, `run.py`, `sources.json`, `.env`)
