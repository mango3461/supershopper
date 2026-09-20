import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export function GET() {
  const provider =
    process.env.SEARCH_PROVIDER || (process.env.OPENAI_API_KEY ? 'openai' : 'everland');

  return NextResponse.json(
    {
      provider,
      searchProviderConfigured: Boolean(process.env.SEARCH_PROVIDER),
      geminiKeyConfigured: Boolean(process.env.GEMINI_API_KEY),
      geminiModelConfigured: Boolean(process.env.GEMINI_MODEL),
      nodeEnv: process.env.NODE_ENV,
    },
    { headers: { 'Cache-Control': 'no-store' } },
  );
}
