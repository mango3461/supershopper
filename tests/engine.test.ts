import { describe, expect, it, vi } from 'vitest';
import {
  benefitSchema,
  dateSchema,
  type BasePrice,
  type BenefitCandidate,
  type PurchaseIntent,
} from '../schemas';
import { mockProfile } from '../lib/profile/mockProfile';
import { evaluateEligibility } from '../lib/benefits/eligibility';
import { calculate } from '../lib/benefits/calculate';
import { deduplicate, rank } from '../lib/benefits/rank';
import { search } from '../lib/search/engine';
import { EverlandProvider, parseCatalog } from '../lib/search/everland';
import { mapConcurrent, type SearchProvider } from '../lib/search/provider';
import { verifyBenefit } from '../lib/ai/openaiProvider';
import { isOfficial } from '../lib/search/evidence';
import { zodTextFormat } from 'openai/helpers/zod';
import { extractionSchema, baseResolutionSchema, intentSchema, planSchema } from '../schemas';

// Synthetic unit-test inputs. Never imported by the production search path.
const today = '2026-09-20';
const intent: PurchaseIntent = {
  merchant: '에버랜드',
  product: '종일권',
  date: today,
  location: null,
  quantity: 1,
};
const context = {
  product: '종일권',
  date: today,
  quantity: 1,
  priceType: '대인',
  channel: '스마트예약',
};
const source = {
  url: 'https://reservation.everland.com/test',
  title: 'TEST ONLY',
  official: true,
  verified: true,
  retrievedAt: '2026-09-20T00:00:00.000Z',
  excerpt: 'Synthetic test evidence 2026-09-01 2026-09-30 20% 60,000원',
};
function candidate(overrides: Partial<BenefitCandidate> = {}): BenefitCandidate {
  return benefitSchema.parse({
    id: 'test',
    title: 'TEST ONLY',
    merchant: '에버랜드',
    provider: 'test',
    category: 'occupation',
    mode: 'personal',
    discount: { type: 'percentage', value: 20, specialPrice: null, cap: null },
    requirements: [
      { field: 'occupation', operator: 'equals', value: '대학생', description: '대학생 대상' },
    ],
    validFrom: '2026-09-01',
    validUntil: '2026-09-30',
    purchaseMethod: 'test',
    stackable: null,
    source,
    confidence: 'high',
    context,
    conditionsComplete: true,
    calculationSafe: true,
    caveats: [],
    ...overrides,
  });
}
const base: BasePrice = { ...context, amount: 60000, currency: 'KRW', source };
const evaluate = (b = candidate(), p = mockProfile, i = intent) =>
  evaluateEligibility(b, p, i, today);

describe('eligibility', () => {
  it('returns confirmed for evidenced matching conditions', () =>
    expect(evaluate().status).toBe('confirmed'));
  it('returns needs_info for missing carrier grade', () =>
    expect(
      evaluate(
        candidate({
          requirements: [
            {
              field: 'carrier.grade',
              operator: 'equals',
              value: 'VIP',
              description: '통신사 등급은?',
            },
          ],
        }),
      ).status,
    ).toBe('needs_info'));
  it('returns not_eligible for known mismatch', () =>
    expect(evaluate(candidate(), { ...mockProfile, occupation: '직장인' }).status).toBe(
      'not_eligible',
    ));
  it('returns unknown for unverified source even with matching conditions', () =>
    expect(evaluate(candidate({ source: { ...source, verified: false } })).status).toBe('unknown'));
  it('does not equate card issuer with exact product', () =>
    expect(
      evaluate(
        candidate({
          requirements: [
            {
              field: 'cards.product',
              operator: 'contains',
              value: '현대카드',
              description: '정확한 카드',
            },
          ],
        }),
      ).status,
    ).toBe('not_eligible'));
  it('unknown operators and unsupported fields need information', () =>
    expect(
      evaluate(
        candidate({
          requirements: [
            { field: 'spend', operator: 'gte', value: 300000, description: '전월 실적 확인' },
          ],
        }),
      ).status,
    ).toBe('needs_info'));
  it('expired and upcoming periods fail for selected date', () => {
    expect(evaluate(candidate({ validUntil: '2026-09-19' })).status).toBe('not_eligible');
    expect(evaluate(candidate({ validFrom: '2026-09-21' })).status).toBe('not_eligible');
  });
  it('missing period or incomplete conditions cannot confirm', () => {
    expect(evaluate(candidate({ validUntil: null })).status).toBe('unknown');
    expect(evaluate(candidate({ conditionsComplete: false })).status).toBe('unknown');
  });
  it('missing visit date surfaces a question', () =>
    expect(evaluate(candidate(), mockProfile, { ...intent, date: null }).missing[0].field).toBe(
      'date',
    ));
});
describe('deterministic arithmetic', () => {
  it('calculates a supported percentage', () =>
    expect(calculate(candidate(), evaluate(), base, intent).finalPrice).toBe(48000));
  it('respects discount cap', () =>
    expect(
      calculate(
        candidate({ discount: { type: 'percentage', value: 20, specialPrice: null, cap: 5000 } }),
        evaluate(),
        base,
        intent,
      ).finalPrice,
    ).toBe(55000));
  it('calculates fixed and special prices', () => {
    expect(
      calculate(
        candidate({ discount: { type: 'fixed', value: 10000, specialPrice: null, cap: null } }),
        evaluate(),
        base,
        intent,
      ).finalPrice,
    ).toBe(50000);
    expect(
      calculate(
        candidate({
          discount: { type: 'special_price', value: null, specialPrice: 42000, cap: null },
        }),
        evaluate(),
        base,
        intent,
      ).savedAmount,
    ).toBe(18000);
  });
  it('never calculates without trusted base, even for special price', () =>
    expect(
      calculate(
        candidate({
          discount: { type: 'special_price', value: null, specialPrice: 42000, cap: null },
        }),
        evaluate(),
        null,
        intent,
      ).finalPrice,
    ).toBeNull());
  it.each(['date', 'product', 'priceType', 'channel'] as const)(
    'rejects mismatching %s context',
    (key) =>
      expect(
        calculate(candidate({ context: { ...context, [key]: null } }), evaluate(), base, intent)
          .finalPrice,
      ).toBeNull(),
  );
  it('does not multiply personal discount across a group', () =>
    expect(
      calculate(candidate(), evaluate(), base, { ...intent, quantity: 2 }).finalPrice,
    ).toBeNull());
  it('does not invent rounding', () =>
    expect(
      calculate(candidate(), evaluate(), { ...base, amount: 60001 }, intent).finalPrice,
    ).toBeNull());
  it('does not calculate unconfirmed eligibility', () =>
    expect(
      calculate(candidate(), { ...evaluate(), status: 'needs_info' }, base, intent).finalPrice,
    ).toBeNull());
  it('rejects rates over 100%', () =>
    expect(
      calculate(
        candidate({ discount: { type: 'percentage', value: 120, specialPrice: null, cap: null } }),
        evaluate(),
        base,
        intent,
      ).finalPrice,
    ).toBeNull());
});
describe('evidence and ranking', () => {
  it('SDK accepts every model output schema as a strict structured format', () => {
    for (const schema of [extractionSchema, baseResolutionSchema, intentSchema, planSchema])
      expect(zodTextFormat(schema, 'schema').strict).toBe(true);
  });
  it('does not treat a user-hosted Naver blog as official evidence', () =>
    expect(isOfficial('https://blog.naver.com/test')).toBe(false));
  it('merges duplicates and prefers official evidence', () =>
    expect(
      deduplicate([candidate({ source: { ...source, official: false } }), candidate()])[0].source
        .official,
    ).toBe(true));
  it('retains conflicts as unknown and never calculates', () =>
    expect(
      deduplicate([
        candidate(),
        candidate({ discount: { type: 'percentage', value: 30, specialPrice: null, cap: null } }),
      ])[0].confidence,
    ).toBe('low'));
  it('separates discovery conditions from best', () => {
    const b = candidate({ mode: 'discovery' });
    const e = calculate(b, { ...evaluate(), status: 'not_eligible' }, base, intent);
    expect(rank([e]).best).toBeNull();
    expect(rank([e]).opportunities).toHaveLength(1);
  });
  it('selects only a priced confirmed benefit', () => {
    const good = calculate(candidate(), evaluate(), base, intent);
    const bad = {
      ...good,
      finalPrice: 1,
      eligibility: { ...good.eligibility, status: 'needs_info' as const },
    };
    expect(rank([bad, good]).best?.finalPrice).toBe(48000);
  });
  it('rejects fabricated quotes and numeric values', () => {
    const page = { ...source, text: source.excerpt, html: '' };
    expect(
      verifyBenefit(candidate({ source: { ...source, excerpt: 'this is a made up quote' } }), [
        page,
      ]),
    ).toBeNull();
    expect(
      verifyBenefit(
        candidate({ discount: { type: 'percentage', value: 90, specialPrice: null, cap: null } }),
        [page],
      )?.discount.type,
    ).toBe('unknown');
  });
  it.each([
    'https://everland.com.evil.com/a',
    'http://everland.com/a',
    'https://localhost/a',
    'https://127.0.0.1',
    'https://everland.com:8080',
    'https://user@everland.com',
  ])('rejects unsafe URLs %s', (url) => expect(isOfficial(url)).toBe(false));
  it('rejects malformed schema and impossible dates', () => {
    expect(benefitSchema.safeParse({ title: 'bad' }).success).toBe(false);
    expect(dateSchema.safeParse('2026-02-30').success).toBe(false);
  });
});
describe('orchestration', () => {
  it('parses Everland and makes personal + discovery plan', async () => {
    const p = new EverlandProvider();
    expect((await p.parseIntent('에버랜드')).merchant).toBe('에버랜드');
    const tasks = await p.planSearch(intent, mockProfile, today);
    expect(tasks.some((t) => t.mode === 'personal')).toBe(true);
    expect(tasks.some((t) => t.mode === 'discovery')).toBe(true);
    expect(tasks.length).toBeLessThanOrEqual(8);
  });
  it('does not silently drop natural language in keyless mode', async () =>
    expect(new EverlandProvider().parseIntent('내일 에버랜드 3명')).rejects.toThrow(
      'LIMITED_QUERY',
    ));
  it('parses real catalog link shape without executing scripts', () =>
    expect(
      parseCatalog(
        `<a onclick="fnCallCalendar('0101','123','getProduct')"><strong>혜택</strong><i>조건</i></a><script>throw 1</script>`,
      )[0].url,
    ).toContain('menu_id=123'));
  it('bounds concurrent work and preserves order', async () => {
    let active = 0;
    let peak = 0;
    const result = await mapConcurrent([1, 2, 3, 4], 2, async (n) => {
      peak = Math.max(peak, ++active);
      await new Promise((r) => setTimeout(r, 4));
      active--;
      return n;
    });
    expect(peak).toBe(2);
    expect(result).toEqual([1, 2, 3, 4]);
  });
  it('isolates malformed output / timeout and filters expired offers', async () => {
    vi.spyOn(console, 'info').mockImplementation(() => {});
    const provider: SearchProvider = {
      name: 'test',
      parseIntent: async () => intent,
      planSearch: async () =>
        ['ok', 'bad', 'timeout'].map((id) => ({
          id,
          category: 'promotion',
          query: id,
          profileEvidence: [],
          mode: 'discovery',
        })),
      resolveBasePrice: async () => ({ basePrice: base, reason: 'test' }),
      search: async (task) => {
        if (task.id === 'timeout') throw new Error('timeout');
        if (task.id === 'bad') return { benefits: [{} as BenefitCandidate], sourceCount: 1 };
        return {
          benefits: [candidate(), candidate({ id: 'expired', validUntil: '2020-01-01' })],
          sourceCount: 1,
        };
      },
    };
    const result = await search({ query: '에버랜드' }, provider, today);
    expect(result.summary.found).toBe(1);
    expect(result.tasks.filter((t) => t.status === 'failed')).toHaveLength(2);
    expect(result.best?.finalPrice).toBe(48000);
    expect(result.warnings).toHaveLength(1);
    vi.restoreAllMocks();
  });
});
