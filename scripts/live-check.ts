import { mkdir, writeFile } from 'node:fs/promises';
import { search } from '../lib/search/engine';
import { audit, safeFailure, withAudit } from '../lib/ai/audit';

async function main() {
  const provider =
    process.env.SEARCH_PROVIDER || (process.env.OPENAI_API_KEY ? 'openai' : 'everland');
  const configured =
    provider === 'gemini'
      ? Boolean(process.env.GEMINI_API_KEY)
      : provider === 'openai'
        ? Boolean(process.env.OPENAI_API_KEY)
        : false;
  if (!configured || !['openai', 'gemini'].includes(provider)) {
    console.error(
      'Live mode requires the selected provider API key and SEARCH_PROVIDER=openai or gemini. No secret values are displayed.',
    );
    process.exitCode = 1;
    return;
  }
  const report = await withAudit(async () => {
    try {
      return await search({ query: process.argv[2] || '에버랜드' });
    } catch (e) {
      audit({ stage: 'pipeline', status: 'failed', ...safeFailure(e) });
      return null;
    }
  });
  const output = JSON.stringify(report, null, 2);
  // Defense in depth: no configured secret value can be printed or persisted.
  const secrets = Object.entries(process.env)
    .filter(([key, value]) => /KEY|TOKEN|SECRET|PASSWORD/i.test(key) && value && value.length >= 8)
    .map(([, value]) => value!);
  const safe = secrets.reduce((s, secret) => s.split(secret).join('[REDACTED]'), output);
  await mkdir('.scratch', { recursive: true });
  await writeFile('.scratch/live-report.json', safe);
  console.log(safe);
  if (!report.result) process.exitCode = 1;
}
main().catch(() => {
  console.error('Live verification failed. No raw errors or secrets are logged.');
  process.exitCode = 1;
});
