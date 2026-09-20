import { load } from 'cheerio';
import {
  benefitSchema,
  intentSchema,
  planSchema,
  type PurchaseIntent,
  type SearchTask,
  type UserProfile,
} from '../../schemas';
import { fetchEvidence, normalizeText } from './evidence';
import type { EvidencePage, SearchProvider, TaskResult } from './provider';

const catalogUrl = 'https://reservation.everland.com/web/el.do?method=productMain';
type Listing = { title: string; description: string; url: string };
export function parseCatalog(html: string): Listing[] {
  const $ = load(html);
  const listings = new Map<string, Listing>();
  $('a[onclick]').each((_, el) => {
    const match = $(el)
      .attr('onclick')
      ?.match(/fnCallCalendar\('(\d+)','(\d+)'/);
    if (!match) return;
    const title = normalizeText($(el).find('strong').text());
    const description = normalizeText($(el).find('i').text());
    if (!title) return;
    const url = `https://reservation.everland.com/web/el.do?method=getProduct&top_menu_id=01&high_menu_id=${match[1]}&menu_id=${match[2]}`;
    listings.set(url, { title, description, url });
  });
  return [...listings.values()];
}
export class EverlandProvider implements SearchProvider {
  readonly name = 'everland-official';
  private catalogPromise?: Promise<EvidencePage>;
  constructor(private readonly signal?: AbortSignal) {}
  private catalog() {
    return (this.catalogPromise ??= fetchEvidence(catalogUrl, this.signal));
  }
  async parseIntent(query: string) {
    if (!/에버랜드|everland/i.test(query)) throw new Error('LIMITED_QUERY');
    // The keyless adapter intentionally accepts only a narrow grammar; never silently discard user constraints.
    const remainder = query.replace(/에버랜드|everland|종일권|\d{4}-\d{2}-\d{2}/gi, '').trim();
    if (remainder) throw new Error('LIMITED_QUERY');
    return intentSchema.parse({
      merchant: '에버랜드',
      product: query.includes('종일권') ? '종일권' : null,
      date: query.match(/\d{4}-\d{2}-\d{2}/)?.[0] ?? null,
      location: null,
      quantity: null,
    });
  }
  async planSearch(intent: PurchaseIntent, profile: UserProfile, today: string) {
    const entries: [SearchTask['category'], string[]][] = [
      ['card', profile.cards.map((c) => `${c.issuer} ${c.product}`)],
      [
        'carrier',
        profile.carrier
          ? [profile.carrier.provider, ...(profile.carrier.grade ? [profile.carrier.grade] : [])]
          : [],
      ],
      ['membership', profile.memberships],
      ['occupation', profile.occupation ? [profile.occupation] : []],
      ['age', profile.age != null ? [`${profile.age}세`] : []],
      ['location', profile.location ? [profile.location] : []],
      ['promotion', []],
    ];
    return planSchema.parse({
      tasks: entries
        .filter(([category, facts]) => category === 'promotion' || facts.length)
        .map(([category, facts]) => ({
          id: category,
          category,
          query: `${intent.merchant} ${facts.join(' ')} ${category === 'promotion' ? '공식 현재 프로모션' : '할인 조건'} ${today}`,
          profileEvidence: facts,
          mode: category === 'promotion' ? 'discovery' : 'personal',
        })),
    }).tasks;
  }
  async search(task: SearchTask, intent: PurchaseIntent): Promise<TaskResult> {
    if (!['card', 'occupation', 'promotion'].includes(task.category))
      return {
        benefits: [],
        sourceCount: 0,
        unsupported: true,
        message:
          '공식 페이지 직접 탐색 모드에서는 이 경로를 지원하지 않습니다. 웹 검색 모드가 필요합니다.',
      };
    const catalog = await this.catalog();
    const listings = parseCatalog(catalog.html);
    const selected = listings
      .filter((l) =>
        task.category === 'card'
          ? /제휴카드 할인|현대카드 M포인트/.test(l.title)
          : task.category === 'occupation'
            ? /대학.*생/.test(l.title)
            : /대인 종일권 특별 우대|문화가 있는 날/.test(l.title),
      )
      .slice(0, 3);
    let readCount = 1;
    const benefits = [];
    for (const listing of selected) {
      const page = await fetchEvidence(listing.url, this.signal);
      readCount++;
      const requirements: import('../../schemas').BenefitCandidate['requirements'] = [];
      if (/대학.*생/.test(listing.title) && page.text.includes('학생'))
        requirements.push({
          field: 'occupation',
          operator: 'in',
          value: listing.title.includes('(원)') ? ['대학생', '대학원생'] : ['대학생'],
          description: '대학(원)생 대상 우대입니다. 학생 신분 증빙을 확인해주세요.',
        });
      if (/대학.*생/.test(listing.title) && page.text.includes('학생증'))
        requirements.push({
          field: 'studentDocument',
          operator: 'unknown',
          value: '',
          description: '입장 시 제시할 유효한 학생 증빙 서류가 있나요?',
        });
      if (/제휴카드/.test(listing.title))
        requirements.push({
          field: 'cardProductEligibility',
          operator: 'unknown',
          value: '',
          description:
            '보유한 정확한 카드 상품의 제휴 대상 여부와 이용실적을 카드사에서 확인해주세요.',
        });
      if (/포인트/.test(listing.title))
        requirements.push({
          field: 'pointBalance',
          operator: 'unknown',
          value: '',
          description:
            '사용 가능한 M포인트와 보유 카드의 사용 자격을 확인해주세요. 포인트 차감은 현금 할인과 다릅니다.',
        });
      requirements.push({
        field: 'offerTerms',
        operator: 'unknown',
        value: '',
        description: '공식 페이지에서 방문일별 유효기간, 대상 및 예약 조건을 확인해주세요.',
      });
      const percentage = !/포인트/.test(listing.title)
        ? page.text.match(/본인(?:은)?\s*(\d{1,2})%/)
        : null;
      const excerptIndex = Math.max(
        0,
        percentage ? page.text.indexOf(percentage[0]) - 150 : page.text.indexOf('안내 및 주의사항'),
      );
      benefits.push(
        benefitSchema.parse({
          id: `everland-${new URL(listing.url).searchParams.get('menu_id')}`,
          title: listing.title,
          merchant: intent.merchant,
          provider: '에버랜드 스마트예약',
          category: task.category,
          mode: task.mode,
          discount: {
            type: percentage ? 'percentage' : 'unknown',
            value: percentage ? Number(percentage[1]) : null,
            specialPrice: null,
            cap: null,
          },
          requirements,
          validFrom: null,
          validUntil: null,
          purchaseMethod: '에버랜드 스마트예약에서 방문일과 상품을 선택하고 조건을 확인하세요.',
          stackable: page.text.includes('중복 적용되지 않습니다') ? false : null,
          source: {
            url: page.url,
            title: listing.title + ' · 에버랜드 공식 예약',
            official: true,
            verified: true,
            retrievedAt: page.retrievedAt,
            excerpt: page.text.slice(excerptIndex, excerptIndex + 650),
          },
          confidence: 'medium',
          context: {
            product: /종일|대학/.test(listing.title) ? '종일권' : null,
            priceType: null,
            date: intent.date,
            channel: '스마트예약',
            quantity: 1,
          },
          conditionsComplete: false,
          calculationSafe: false,
          caveats: [
            '공식 상세 페이지를 읽었지만 이미지·동적 예약 영역의 전체 조건과 기간을 확정하지 못했습니다.',
            /포인트/.test(listing.title)
              ? '포인트 잔액을 결제 비용으로 고려해야 하므로 현금 할인 가격으로 계산하지 않습니다.'
              : '목록의 시작 가격과 할인 안내는 방문일별 확정 결제가가 아닙니다.',
          ],
        }),
      );
    }
    return { benefits, sourceCount: readCount };
  }
  async resolveBasePrice(intent: PurchaseIntent) {
    const catalog = await this.catalog();
    const regular = parseCatalog(catalog.html).find((l) => l.title === '종일권');
    if (regular) await fetchEvidence(regular.url, this.signal);
    return {
      basePrice: null,
      reason: !intent.date
        ? '방문일이 없어 날짜별 정가를 정할 수 없어요. 방문일을 선택하고 공식 예약 요금을 확인해주세요.'
        : '공식 정가 페이지의 날짜·연령별 예약 금액을 신뢰할 수 있게 읽지 못했어요. 공식 예약 화면에서 확인해주세요.',
    };
  }
}
