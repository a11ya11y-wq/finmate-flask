# FinMate Frontend

Vite + React + TypeScript frontend for FinMate. Uses Zustand for state, Tailwind + Shadcn-style components, and Recharts.

## Quick start

1. Install dependencies.
2. Run dev server.

```powershell
npm install
npm run dev
```

The API base URL defaults to `http://localhost:5000/api/v1`. You can override it via:

```powershell
$Env:VITE_API_BASE_URL="http://localhost:5000/api/v1"
```

## Tests

```powershell
npm run test
```

