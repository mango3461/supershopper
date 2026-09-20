import { AsyncLocalStorage } from 'node:async_hooks';

export type AuditEvent = {
  stage: string;
  status: 'complete' | 'failed' | 'skipped';
  model?: string;
  latencyMs?: number;
  httpStatus?: number;
  errorType?: string;
  errorCode?: string;
  limitReason?: 'quota_or_billing' | 'request_rate' | 'unspecified';
  sourceUrls?: string[];
  webSearchCalls?: number;
  count?: number;
};
const auditStorage = new AsyncLocalStorage<AuditEvent[]>();
export function audit(event: AuditEvent) {
  auditStorage.getStore()?.push(event);
}
export async function withAudit<T>(run: () => Promise<T>) {
  const events: AuditEvent[] = [];
  return auditStorage.run(events, async () => ({ result: await run(), events }));
}
// Never serialize SDK errors, messages, headers, request bodies or environment variables.
export function safeFailure(
  error: unknown,
): Pick<AuditEvent, 'httpStatus' | 'errorType' | 'errorCode' | 'limitReason'> {
  const obj = error && typeof error === 'object' ? (error as Record<string, unknown>) : {};
  const allowed = [
    'APIError',
    'AuthenticationError',
    'PermissionDeniedError',
    'RateLimitError',
    'BadRequestError',
    'APIConnectionError',
    'APIConnectionTimeoutError',
    'APIUserAbortError',
    'TimeoutError',
    'AbortError',
    'ZodError',
  ];
  const nested =
    obj.error && typeof obj.error === 'object' ? (obj.error as Record<string, unknown>) : {};
  const errorName = error instanceof Error ? error.constructor.name : obj.name;
  const code = obj.code ?? nested.code ?? nested.type;
  const message = typeof obj.message === 'string' ? obj.message : '';
  const quotaCodes = [
    'insufficient_quota',
    'billing_hard_limit_reached',
    'credit_balance_exhausted',
    'organization_spend_limit_exceeded',
    'project_spend_limit_exceeded',
    'organization_usage_limit_exceeded',
  ];
  return {
    httpStatus: typeof obj.status === 'number' ? obj.status : undefined,
    errorType:
      typeof errorName === 'string' && allowed.includes(errorName)
        ? errorName
        : obj.status === 429
          ? 'RateLimitError'
          : obj.status === 400
            ? 'BadRequestError'
            : 'UnclassifiedProviderError',
    errorCode:
      typeof code === 'string' &&
      [
        ...quotaCodes,
        'rate_limit_exceeded',
        'slow_down',
        'invalid_api_key',
        'model_not_found',
        'invalid_json_schema',
        'unsupported_parameter',
      ].includes(code)
        ? code
        : undefined,
    limitReason:
      obj.status === 429
        ? (typeof code === 'string' && quotaCodes.includes(code)) ||
          /quota|billing|credit|balance/i.test(message)
          ? 'quota_or_billing'
          : /rate.limit|requests per|tokens per/i.test(message)
            ? 'request_rate'
            : 'unspecified'
        : undefined,
  };
}
