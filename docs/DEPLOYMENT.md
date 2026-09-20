# Production deployment

## Required runtime configuration

Set these variables in the hosting platform's server-side environment settings. Do not put provider keys in `NEXT_PUBLIC_*` variables.

| Variable | Required when | Notes |
|---|---|---|
| `SEARCH_PROVIDER` | Always | Use `openai`, `gemini`, or `everland`. Set it explicitly in production. |
| `OPENAI_API_KEY` | `SEARCH_PROVIDER=openai` | Server-only secret. |
| `OPENAI_MODEL` | Optional for OpenAI | Defaults to `gpt-5-mini`. |
| `GEMINI_API_KEY` | `SEARCH_PROVIDER=gemini` | Server-only secret. |
| `GEMINI_MODEL` | Optional for Gemini | Defaults to `gemini-2.5-flash`. |
| `SEARCH_CONCURRENCY` | Optional | Defaults to `3`; controls search-task concurrency. |

`everland` is the keyless official Everland provider. It is a live provider and is not a fixture mode. The profile used by the initial demo is only the documented mock profile; search evidence and prices still come from the provider.

## Build and run

```bash
npm ci
npm run build
npm run start
```

The application listens on the platform-provided `PORT` (Next.js defaults to `3000`). Check `GET /` after startup, then exercise `POST /api/search` only after the selected provider credentials and quota are configured.

For Vercel, import the repository, set the variables above in Project Settings, and use the default Next.js build command. `.vercelignore` excludes local environment files from the upload context.

## Safety checks

- `.env.local` is ignored by the repository and excluded from Vercel upload context. Keep production values in the platform secret manager.
- Provider keys are read only in server modules. The client bundle contains no provider key values.
- A provider error, quota error, or failed evidence task is surfaced as an error or warning. The engine does not fall back to fixture discounts.
- A final `내 가격` is returned only when a trusted base price, confirmed eligibility, and a safe deterministic calculation are all available. Otherwise the price remains unavailable.
- Keep the selected provider explicit; do not rely on implicit provider selection in production.
