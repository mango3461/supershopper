import {
  baseResolutionSchema,
  benefitSchema,
  intentSchema,
  planSchema,
  profileSchema,
  requestSchema,
  responseSchema,
  type TaskTrace,
} from '../../schemas';
import { mockProfile } from '../profile/mockProfile';
import { evaluateEligibility } from '../benefits/eligibility';
import { calculate } from '../benefits/calculate';
import { deduplicate, rank } from '../benefits/rank';
import { EverlandProvider } from './everland';
import { OpenAIProvider } from '../ai/openaiProvider';
import { GeminiProvider } from '../ai/geminiProvider';
import { mapConcurrent, todayKorea, type SearchProvider } from './provider';

export function createProvider(signal?: AbortSignal): SearchProvider {
  const provider =
    process.env.SEARCH_PROVIDER || (process.env.OPENAI_API_KEY ? 'openai' : 'everland');
  if (provider === 'openai') return new OpenAIProvider(signal);
  if (provider === 'gemini') return new GeminiProvider(signal);
  if (provider !== 'everland') throw new Error('UNKNOWN_PROVIDER');
  return new EverlandProvider(signal);
}
export async function search(input: unknown, provider?: SearchProvider, today = todayKorea()) {
  const start = Date.now();
  const request = requestSchema.parse(input);
  const active = provider ?? createProvider(AbortSignal.timeout(150000));
  const profile = profileSchema.parse(request.profile ?? mockProfile);
  const parsed = intentSchema.parse(await active.parseIntent(request.query, today));
  const intent = intentSchema.parse({ ...parsed, date: request.visitDate ?? parsed.date });
  const plan = planSchema.parse({ tasks: await active.planSearch(intent, profile, today) });
  const traces: TaskTrace[] = [];
  const warnings: string[] =
    active.name === 'everland-official'
      ? [
          '공식 페이지 직접 탐색 모드 · 에버랜드의 일부 경로만 지원해요. 전체 웹 검색 결과가 아니며, 이미지 속 조건은 확인이 필요해요.',
        ]
      : [];
  const basePromise = active
    .resolveBasePrice(intent, profile, today)
    .then((result) => baseResolutionSchema.parse(result))
    .catch(() => ({
      basePrice: null,
      reason: '정가 조회에 실패했어요. 확인되지 않은 금액은 계산하지 않아요.',
    }));
  const batches = await mapConcurrent(
    plan.tasks,
    Math.min(4, Math.max(1, Number(process.env.SEARCH_CONCURRENCY) || 3)),
    async (task) => {
      const startTask = Date.now();
      try {
        const result = await active.search(task, intent, today);
        const benefits = result.benefits
          .map((b) => benefitSchema.parse(b))
          .filter((b) => !b.validUntil || b.validUntil >= today);
        traces.push({
          id: task.id,
          category: task.category,
          query: task.query,
          status: result.unsupported ? 'unsupported' : 'complete',
          sourceCount: result.sourceCount,
          found: benefits.length,
          latencyMs: Date.now() - startTask,
          message: result.message ?? null,
        });
        return benefits;
      } catch {
        traces.push({
          id: task.id,
          category: task.category,
          query: task.query,
          status: 'failed',
          sourceCount: 0,
          found: 0,
          latencyMs: Date.now() - startTask,
          message: '탐색 시간 초과 또는 출처·응답 검증 실패. 이 경로의 혜택은 표시하지 않았어요.',
        });
        return [];
      }
    },
  );
  const base = await basePromise;
  if (traces.some((t) => t.status === 'failed'))
    warnings.push('일부 할인 경로를 확인하지 못했어요. 확인된 나머지 결과만 표시합니다.');
  const items = deduplicate(batches.flat()).map((b) =>
    calculate(b, evaluateEligibility(b, profile, intent, today), base.basePrice, intent),
  );
  for (const trace of traces)
    console.info(
      JSON.stringify({
        event: 'search_task',
        category: trace.category,
        latencyMs: trace.latencyMs,
        sourceCount: trace.sourceCount,
        extractionStatus: trace.status,
      }),
    );
  return responseSchema.parse({
    merchant: intent.merchant,
    intent,
    basePrice: base.basePrice,
    basePriceReason: base.reason,
    summary: {
      searched: traces.filter((t) => t.status !== 'unsupported').length,
      found: items.length,
      confirmed: items.filter((i) => i.eligibility.status === 'confirmed').length,
      needsInfo: items.filter((i) => i.eligibility.status === 'needs_info').length,
    },
    ...rank(items),
    tasks: plan.tasks.map((t) => traces.find((trace) => trace.id === t.id)!),
    warnings,
    provider: active.name,
    checkedAt: new Date().toISOString(),
    elapsedMs: Date.now() - start,
  });
}
