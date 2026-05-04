# Paper Lens Web

Next.js frontend for Paper Lens. It talks to `paper-lens-backend` over REST and SSE.

## Setup

```bash
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

The default backend is `http://localhost:8765`. Change `NEXT_PUBLIC_BACKEND_URL` in `.env.local` if the backend runs elsewhere.

## Checks

```bash
npm run lint
npx tsc --noEmit
```
