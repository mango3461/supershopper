import { z } from 'zod';
import {
  baseResolutionSchema,
  extractionSchema,
  intentSchema,
  planSchema,
  type PurchaseIntent,
  type SearchTask,
  type UserProfile,
  type BenefitCandidate,
} from '../../schemas';
import {
  queryParserPrompt,
  searchPlannerPrompt,
  webSearchPrompt,
  benefitExtractorPrompt,
  basePricePrompt,
} from '../../prompts';
import { createAi, model, structured } from './client';
import { audit, safeFailure } from './audit';
import { fetchEvidence, isOfficial, normalizeText, officialDomains } from '../search/evidence';
import { mapConcurrent, type EvidencePage, type SearchProvider } from '../search/provider';

const searchOutputSchema = z.object({
  output: z.array(
    z
      .object({
        type: z.string(),
        content: z
          .array(
            z
              .object({
                type: z.string(),
                annotations: z
                  .array(z.object({ type: z.string(), url: z.string().optional() }).passthrough())
                  .optional(),
              })
              .passthrough(),
          )
          .optional(),
      })
      .passthrough(),
  ),
});
function hasNumber(quote: string, value: number) {
  return new RegExp(`(^|[^0-9])${value}([^0-9]|$)`).test(quote.replaceAll(',', ''));
}
function hasDate(quote: string, date: string) {
  return quote
    .replace(
      /(\d{4})[.년/ -]+(\d{1,2})[.월/ -]+(\d{1,2})일?/g,
      (_, y, m, d) => `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`,
    )
    .includes(date);
}
export function verifyBenefit(b: BenefitCandidate, pages: EvidencePage[]): BenefitCandidate | null {
  const page = pages.find((p) => p.url === b.source.url);
  const quote = normalizeText(b.source.excerpt);
  if (!page || quote.length < 12 || !page.text.includes(quote)) return null;
  const monetary = b.discount.type === 'special_price' ? b.discount.specialPrice : b.discount.value;
  const numbersGrounded =
    (monetary === null || hasNumber(quote, monetary)) &&
    (b.discount.cap === null || hasNumber(quote, b.discount.cap));
  const datesGrounded =
    (!b.validFrom || hasDate(quote, b.validFrom)) &&
    (!b.validUntil || hasDate(quote, b.validUntil));
  if (!numbersGrounded || !datesGrounded)
    return {
      ...b,
      discount: { type: 'unknown', value: null, specialPrice: null, cap: null },
      validFrom: null,
      validUntil: null,
      source: {
        ...b.source,
        official: true,
        verified: true,
        retrievedAt: page.retrievedAt,
        excerpt: quote,
      },
      confidence: 'low',
      conditionsComplete: false,
      calculationSafe: false,
      caveats: [...b.caveats, '추출한 수치 또는 기간을 인용문에서 검증하지 못했습니다.'],
    };
  return {
    ...b,
    source: {
      ...b.source,
      official: isOfficial(page.url),
      verified: true,
      retrievedAt: page.retrievedAt,
      excerpt: quote,
    },
  };
}
export class OpenAIProvider implements SearchProvider {
  readonly name = 'openai-web-search';
  private readonly client = createAi();
  constructor(private readonly signal?: AbortSignal) {}
  async parseIntent(query: string, today: string) {
    return structured(
      this.client,
      intentSchema,
      'purchase_intent',
      queryParserPrompt,
      { CURRENT_DATE: today, USER_QUERY: query },
      this.signal,
    );
  }
  async planSearch(intent: PurchaseIntent, profile: UserProfile, today: string) {
    return (
      await structured(
        this.client,
        planSchema,
        'search_plan',
        searchPlannerPrompt,
        { PURCHASE_INTENT: intent, USER_PROFILE: profile, CURRENT_DATE: today },
        this.signal,
      )
    ).tasks;
  }
  private async pages(query: string): Promise<EvidencePage[]> {
    const started = Date.now();
    try {
      const raw = await this.client.responses.create(
        {
          model: model(),
          store: false,
          tools: [{ type: 'web_search', filters: { allowed_domains: officialDomains } }],
          tool_choice: 'required',
          input: [
            { role: 'system', content: webSearchPrompt },
            { role: 'user', content: query },
          ],
        },
        { signal: this.signal },
      );
      // The generated prose is never consumed. Validate only citation metadata, then independently fetch each page.
      const output = searchOutputSchema.parse(raw);
      audit({
        stage: 'web_search',
        status: 'complete',
        model: raw.model,
        webSearchCalls: output.output.filter((o) => o.type === 'web_search_call').length,
        latencyMs: Date.now() - started,
      });
      const urls = [
        ...new Set(
          output.output
            .flatMap((o) => o.content ?? [])
            .flatMap((c) => c.annotations ?? [])
            .flatMap((a) =>
              a.type === 'url_citation' && a.url && isOfficial(a.url) ? [a.url] : [],
            ),
        ),
      ].slice(0, 3);
      audit({ stage: 'search_sources', status: 'complete', sourceUrls: urls });
      const pages = await mapConcurrent(urls, 2, async (url) => {
        try {
          return await fetchEvidence(url, this.signal);
        } catch (e) {
          audit({ stage: 'source_fetch', status: 'failed', sourceUrls: [url], ...safeFailure(e) });
          return null;
        }
      });
      const readable = pages.filter((p): p is EvidencePage => p !== null);
      audit({ stage: 'source_fetch', status: 'complete', sourceUrls: readable.map((p) => p.url) });
      return readable;
    } catch (e) {
      audit({
        stage: 'web_search',
        status: 'failed',
        ...safeFailure(e),
        latencyMs: Date.now() - started,
      });
      throw e;
    }
  }
  async search(task: SearchTask, intent: PurchaseIntent, today: string) {
    const pages = await this.pages(task.query);
    if (!pages.length)
      return {
        benefits: [],
        sourceCount: 0,
        message:
          '검색 결과의 공식 상세 본문을 읽지 못했습니다. 스니펫만으로 혜택을 확정하지 않습니다.',
      };
    const extracted = await structured(
      this.client,
      extractionSchema,
      'benefit_extraction',
      benefitExtractorPrompt,
      {
        SEARCH_TASK: task,
        PURCHASE_INTENT: intent,
        CURRENT_DATE: today,
        PAGES: pages.map((p) => ({
          url: p.url,
          title: p.title,
          text: p.text,
          retrievedAt: p.retrievedAt,
        })),
      },
      this.signal,
    );
    const benefits = extracted.benefits
      .map((b) => verifyBenefit({ ...b, mode: task.mode }, pages))
      .filter((b): b is BenefitCandidate => b !== null && b.merchant === intent.merchant);
    audit({ stage: 'benefit_verified', status: 'complete', count: benefits.length });
    return { benefits, sourceCount: pages.length };
  }
  async resolveBasePrice(intent: PurchaseIntent, profile: UserProfile, today: string) {
    if (!intent.date || !intent.product || intent.quantity !== 1)
      return {
        basePrice: null,
        reason: '방문일·정확한 상품·1인 구매 여부가 확인되어야 정가와 내 가격을 계산할 수 있어요.',
      };
    const pages = await this.pages(
      `${intent.merchant} ${intent.product} ${intent.date} ${profile.age ?? ''}세 공식 정가 이용요금`,
    );
    const resolved = await structured(
      this.client,
      baseResolutionSchema,
      'base_price',
      basePricePrompt,
      {
        PURCHASE_INTENT: intent,
        USER_PROFILE: profile,
        CURRENT_DATE: today,
        PAGES: pages.map((p) => ({
          url: p.url,
          title: p.title,
          text: p.text,
          retrievedAt: p.retrievedAt,
        })),
      },
      this.signal,
    );
    const b = resolved.basePrice;
    if (!b) return resolved;
    const page = pages.find((p) => p.url === b.source.url);
    const quote = normalizeText(b.source.excerpt);
    if (
      !page ||
      quote.length < 12 ||
      !page.text.includes(quote) ||
      !hasNumber(quote, b.amount) ||
      !hasDate(quote, intent.date) ||
      b.date !== intent.date ||
      b.product !== intent.product ||
      b.quantity !== 1
    )
      return {
        basePrice: null,
        reason: '정가의 수치·날짜·상품 문맥을 공식 원문에서 검증하지 못했어요.',
      };
    return {
      ...resolved,
      basePrice: {
        ...b,
        source: { ...b.source, official: true, verified: true, retrievedAt: page.retrievedAt },
      },
    };
  }
}
