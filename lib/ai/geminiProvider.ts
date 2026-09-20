import { GoogleGenAI } from '@google/genai';
import { toJSONSchema, z } from 'zod';
import {
  baseResolutionSchema,
  extractionSchema,
  intentSchema,
  planSchema,
  type BenefitCandidate,
  type PurchaseIntent,
  type SearchTask,
  type UserProfile,
} from '../../schemas';
import {
  benefitExtractorPrompt,
  basePricePrompt,
  queryParserPrompt,
  searchPlannerPrompt,
} from '../../prompts';
import { fetchEvidence, isOfficial, normalizeText } from '../search/evidence';
import { audit, safeFailure } from './audit';
import type { EvidencePage, SearchProvider } from '../search/provider';
import { verifyBenefit } from './openaiProvider';

const geminiModel = () => process.env.GEMINI_MODEL || 'gemini-2.5-flash';
const schemaForGemini = (schema: z.ZodType) => {
  const json = toJSONSchema(schema, { target: 'draft-07' }) as Record<string, unknown>;
  delete json.$schema;
  return json;
};
type GeminiResponse = {
  text?: string;
  candidates?: Array<{
    groundingMetadata?: {
      webSearchQueries?: string[];
      groundingChunks?: Array<{ web?: { uri?: string; title?: string } }>;
    };
  }>;
};
export class GeminiProvider implements SearchProvider {
  readonly name = 'gemini-google-search';
  private readonly client = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
  constructor(private readonly signal?: AbortSignal) {
    if (!process.env.GEMINI_API_KEY) throw new Error('GEMINI_NOT_CONFIGURED');
  }
  private async json<T extends z.ZodType>(
    schema: T,
    name: string,
    prompt: string,
    input: unknown,
    grounded: boolean,
    useSchema = true,
  ): Promise<{ parsed: z.infer<T>; response: GeminiResponse }> {
    const started = Date.now();
    try {
      const response = await this.client.models.generateContent({
        model: geminiModel(),
        contents: `${prompt}\n\nINPUT_JSON:\n${JSON.stringify(input)}`,
        config: {
          temperature: 0,
          responseMimeType: 'application/json',
          ...(useSchema ? { responseSchema: schemaForGemini(schema) } : {}),
          ...(grounded ? { tools: [{ googleSearch: {} }] } : {}),
        },
      });
      if (this.signal?.aborted) throw new DOMException('aborted', 'AbortError');
      const parsed = schema.parse(JSON.parse(response.text || '{}'));
      const raw = response as unknown as GeminiResponse;
      audit({
        stage: `gemini_${name}`,
        status: 'complete',
        model: geminiModel(),
        latencyMs: Date.now() - started,
        webSearchCalls: raw.candidates?.[0]?.groundingMetadata?.webSearchQueries?.length,
      });
      return { parsed, response: raw };
    } catch (e) {
      audit({
        stage: `gemini_${name}`,
        status: 'failed',
        model: geminiModel(),
        ...safeFailure(e),
        latencyMs: Date.now() - started,
      });
      throw e;
    }
  }
  private citations(response: GeminiResponse) {
    const unique = new Map<string, { uri: string; title?: string }>();
    for (const chunk of response.candidates?.[0]?.groundingMetadata?.groundingChunks ?? []) {
      const web = chunk.web;
      if (web?.uri && /^https:\/\//.test(web.uri))
        unique.set(web.uri, { uri: web.uri, title: web.title });
    }
    return [...unique.values()];
  }
  private async groundedPages(query: string) {
    const started = Date.now();
    let response: GeminiResponse;
    try {
      const raw = await this.client.models.generateContent({
        model: geminiModel(),
        contents: `Search Google for current official merchant or benefit-provider pages for this task. Prefer official sources, do not use blogs or aggregators, and do not invent facts. Return a concise summary with citations. TASK: ${query}`,
        config: { temperature: 0, tools: [{ googleSearch: {} }] },
      });
      response = raw as unknown as GeminiResponse;
      audit({
        stage: 'gemini_source_search',
        status: 'complete',
        model: geminiModel(),
        latencyMs: Date.now() - started,
        webSearchCalls: response.candidates?.[0]?.groundingMetadata?.webSearchQueries?.length,
      });
    } catch (e) {
      audit({
        stage: 'gemini_source_search',
        status: 'failed',
        model: geminiModel(),
        ...safeFailure(e),
        latencyMs: Date.now() - started,
      });
      throw e;
    }
    const urls = this.citations(response)
      .map((c) => c?.uri)
      .filter((url): url is string => Boolean(url))
      .slice(0, 6);
    const pages = await Promise.all(
      urls.map(async (url) => {
        try {
          let resolved = url;
          if (!isOfficial(resolved)) {
            const redirect = await fetch(resolved, {
              redirect: 'follow',
              signal: this.signal
                ? AbortSignal.any([this.signal, AbortSignal.timeout(8000)])
                : AbortSignal.timeout(8000),
            });
            resolved = redirect.url;
          }
          if (!isOfficial(resolved)) return null;
          return await fetchEvidence(resolved, this.signal);
        } catch (e) {
          audit({
            stage: 'gemini_source_fetch',
            status: 'failed',
            sourceUrls: [url],
            ...safeFailure(e),
          });
          return null;
        }
      }),
    );
    audit({
      stage: 'gemini_grounding_sources',
      status: 'complete',
      sourceUrls: pages.filter((p): p is EvidencePage => p !== null).map((p) => p.url),
    });
    return pages.filter((p): p is EvidencePage => p !== null);
  }
  async parseIntent(query: string, today: string) {
    return (
      await this.json(
        intentSchema,
        'intent',
        queryParserPrompt,
        { CURRENT_DATE: today, USER_QUERY: query },
        false,
      )
    ).parsed;
  }
  async planSearch(intent: PurchaseIntent, profile: UserProfile, today: string) {
    return (
      await this.json(
        planSchema,
        'plan',
        searchPlannerPrompt,
        { PURCHASE_INTENT: intent, USER_PROFILE: profile, CURRENT_DATE: today },
        false,
      )
    ).parsed.tasks;
  }
  async search(task: SearchTask, intent: PurchaseIntent, today: string) {
    const pages = await this.groundedPages(task.query);
    if (!pages.length)
      return {
        benefits: [],
        sourceCount: 0,
        message: 'Google Search Grounding 결과에서 읽을 수 있는 공식 페이지를 찾지 못했습니다.',
      };
    const extraction = await this.json(
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
      false,
      false,
    );
    const groundedUrls = new Set(pages.map((p) => p.url));
    const benefits = extraction.parsed.benefits
      .map((b) => verifyBenefit({ ...b, mode: task.mode }, pages))
      .filter((b): b is BenefitCandidate =>
        Boolean(b && b.merchant === intent.merchant && groundedUrls.has(b.source.url)),
      );
    audit({ stage: 'gemini_benefit_verified', status: 'complete', count: benefits.length });
    return { benefits, sourceCount: pages.length };
  }
  async resolveBasePrice(intent: PurchaseIntent, profile: UserProfile, today: string) {
    if (!intent.date || !intent.product || intent.quantity !== 1)
      return {
        basePrice: null,
        reason: '방문일·정확한 상품·1인 구매 여부가 확인되어야 정가와 내 가격을 계산할 수 있어요.',
      };
    const pages = await this.groundedPages(
      `${intent.merchant} ${intent.product} ${intent.date} ${profile.age ?? ''}세 공식 정가 이용요금`,
    );
    if (!pages.length)
      return {
        basePrice: null,
        reason: 'Google Search Grounding에서 공식 정가 페이지를 확인하지 못했어요.',
      };
    const resolved = (
      await this.json(
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
        false,
        false,
      )
    ).parsed;
    if (!resolved.basePrice) return resolved;
    const page = pages.find((p) => p.url === resolved.basePrice?.source.url);
    const quote = normalizeText(resolved.basePrice.source.excerpt);
    if (!page || !page.text.includes(quote) || resolved.basePrice.source.url !== page.url)
      return { basePrice: null, reason: '정가 인용문을 공식 원문에서 검증하지 못했어요.' };
    return {
      ...resolved,
      basePrice: {
        ...resolved.basePrice,
        source: {
          ...resolved.basePrice.source,
          official: true,
          verified: true,
          retrievedAt: page.retrievedAt,
        },
      },
    };
  }
}
