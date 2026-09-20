import { describe, expect, it } from 'vitest';
import { audit, safeFailure, withAudit } from '../lib/ai/audit';

describe('secret-safe live diagnostics', () => {
  it('never returns provider error messages, headers or unknown error codes', () => {
    const diagnostic = safeFailure({
      status: 429,
      message: 'quota exceeded SENSITIVE_SENTINEL',
      code: 'SENSITIVE_SENTINEL',
      headers: { authorization: 'SENSITIVE_SENTINEL' },
    });
    expect(diagnostic.httpStatus).toBe(429);
    expect(diagnostic.limitReason).toBe('quota_or_billing');
    expect(JSON.stringify(diagnostic)).not.toContain('SENSITIVE_SENTINEL');
  });
  it('retains only recognized provider error codes', () => {
    expect(safeFailure({ status: 429, code: 'credit_balance_exhausted' }).limitReason).toBe(
      'quota_or_billing',
    );
    expect(safeFailure({ status: 429, error: { code: 'insufficient_quota' } }).errorCode).toBe(
      'insufficient_quota',
    );
    expect(safeFailure({ status: 429, message: 'Request rate limit reached' }).limitReason).toBe(
      'request_rate',
    );
  });
  it('isolates audit metadata between concurrent requests', async () => {
    const runs = await Promise.all(
      [1, 2].map((n) =>
        withAudit(async () => {
          await Promise.resolve();
          audit({ stage: `test-${n}`, status: 'complete' });
          return n;
        }),
      ),
    );
    expect(runs[0].events.map((e) => e.stage)).toEqual(['test-1']);
    expect(runs[1].events.map((e) => e.stage)).toEqual(['test-2']);
  });
});
