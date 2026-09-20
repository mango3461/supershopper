'use client';
import { useEffect, useState } from 'react';
import {
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Check,
  CircleHelp,
  ExternalLink,
  LoaderCircle,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Ticket,
  TriangleAlert,
  X,
} from 'lucide-react';
import {
  responseSchema,
  type EvaluatedBenefit,
  type SearchResponse,
  type UserProfile,
} from '../schemas';
import { useProfile } from '../lib/profile/store';
import { SearchBar } from './SearchBar';
import { ProfileSummary } from './ProfileSummary';
import { Drawer } from './Drawer';
import { BenefitDetail, discountLabel, money, statusLabels } from './BenefitDetail';

const categories: Record<string, string> = {
  card: '카드 혜택',
  carrier: '통신사',
  membership: '멤버십',
  occupation: '학생·신분',
  age: '연령',
  location: '지역',
  promotion: '공식 프로모션',
};
export function SearchClient({ query }: { query: string }) {
  const { profile } = useProfile();
  const [visitDate, setVisitDate] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const [revision, setRevision] = useState(0);
  return (
    <main id="main" className="search-page">
      <div className="search-top">
        <SearchBar initial={query} compact />
        <button className="mobile-profile secondary-button" onClick={() => setProfileOpen(true)}>
          <SlidersHorizontal size={17} />내 혜택 보기
        </button>
      </div>
      <div className="results-layout">
        <div className="results-main">
          <div className="result-heading">
            <div>
              <span className="eyebrow">YOUR PERSONAL PRICE</span>
              <h1>
                {query}
                <span>의 내 가격</span>
              </h1>
            </div>
            <label className="date-picker">
              <CalendarDays size={16} />
              <span className="sr-only">방문일</span>
              <input
                type="date"
                aria-label="방문일"
                value={visitDate}
                onChange={(e) => setVisitDate(e.target.value)}
              />
              <span className="date-hint">{visitDate ? '방문일' : '방문일 선택'}</span>
            </label>
          </div>
          <ResultsRequest
            key={`${query}-${visitDate}-${JSON.stringify(profile)}-${revision}`}
            query={query}
            profile={profile}
            visitDate={visitDate}
            onRetry={() => setRevision((n) => n + 1)}
          />
        </div>
        <aside className="result-sidebar">
          <ProfileSummary />
          <div className="sidebar-note">
            <ShieldCheck size={23} />
            <h3>근거가 있어야, 좋은 가격.</h3>
            <p>
              검색 결과보다 공식 본문을 확인해요.
              <br />
              확인되지 않은 조건은 그대로 알려드려요.
            </p>
          </div>
        </aside>
      </div>
      {profileOpen && (
        <Drawer title="내 혜택" onClose={() => setProfileOpen(false)}>
          <ProfileSummary />
        </Drawer>
      )}
    </main>
  );
}
function ResultsRequest({
  query,
  profile,
  visitDate,
  onRetry,
}: {
  query: string;
  profile: UserProfile;
  visitDate: string;
  onRetry: () => void;
}) {
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    const run = async () => {
      try {
        const response = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, profile, ...(visitDate ? { visitDate } : {}) }),
          signal: AbortSignal.any([controller.signal, AbortSignal.timeout(155000)]),
        });
        const json = await response.json();
        if (!response.ok)
          throw new Error(
            typeof json.error?.message === 'string' ? json.error.message : '검색에 실패했어요.',
          );
        setResult(responseSchema.parse(json));
      } catch (e) {
        if (!controller.signal.aborted)
          setError(
            e instanceof Error && e.name === 'TimeoutError'
              ? '검색 시간이 초과되었어요. 다시 시도해주세요.'
              : e instanceof Error
                ? e.message
                : '검색에 실패했어요.',
          );
      }
    };
    void run();
    return () => controller.abort();
  }, [query, profile, visitDate]);
  if (error)
    return (
      <div className="error-state" role="alert">
        <TriangleAlert size={32} />
        <h2>검색을 마무리하지 못했어요</h2>
        <p>{error}</p>
        <button className="primary-button" onClick={onRetry}>
          다시 검색하기
          <ArrowRight size={17} />
        </button>
      </div>
    );
  if (!result)
    return (
      <section className="loading-state" aria-live="polite" aria-busy="true">
        <div className="loading-icon">
          <Search size={30} />
        </div>
        <span className="eyebrow">FINDING YOUR BENEFITS</span>
        <h2>내게 맞는 할인 경로를 찾고 있어요</h2>
        <p>공식 출처를 읽고, 적용 조건을 하나씩 확인해요.</p>
        <div className="loading-paths">
          {Object.entries(categories).map(([key, label]) => (
            <div key={key}>
              <span>{label}</span>
              <LoaderCircle className="spin" size={15} />
              <small>탐색 요청 중</small>
            </div>
          ))}
        </div>
        <p className="privacy-note">경로별 실제 탐색 결과는 완료 후 표시됩니다.</p>
      </section>
    );
  return <Results result={result} />;
}
function Results({ result }: { result: SearchResponse }) {
  const [selected, setSelected] = useState<EvaluatedBenefit | null>(null);
  const [filter, setFilter] = useState('all');
  const visible = result.alternatives.filter(
    (b) => filter === 'all' || b.eligibility.status === filter,
  );
  return (
    <>
      <div className="result-meta">
        <span>
          <Check size={15} />
          {result.summary.searched}개 경로 탐색 · {result.summary.found}개 후보
        </span>
        <span>
          {new Date(result.checkedAt).toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Asia/Seoul',
          })}{' '}
          확인
        </span>
      </div>
      {result.warnings.map((w, i) => (
        <div className="notice" key={i}>
          <CircleHelp size={17} />
          <p>{w}</p>
        </div>
      ))}
      <section className={`best-card ${result.best ? 'has-price' : ''}`}>
        <div className="best-card-top">
          <span>
            <Sparkles size={17} />
            MY PRICE
          </span>
          <span className="best-label">
            {result.best ? '확인된 후보 중 최저가' : '확실한 가격만 보여드려요'}
          </span>
        </div>
        <p className="best-caption">{result.merchant} · 내 가격</p>
        <h2>
          {result.best ? (
            <>
              {money(result.best.finalPrice!)}
              <small>예상 결제가</small>
            </>
          ) : (
            <>
              아직 확인이 필요해요<span className="price-dash">— 원</span>
            </>
          )}
        </h2>
        <p className="best-description">
          {result.best
            ? `${result.best.title} · 정가 대비 ${money(result.best.savedAmount!)} 절약`
            : result.basePriceReason}
        </p>
        {result.best ? (
          <button className="primary-button" onClick={() => setSelected(result.best)}>
            할인받는 방법
            <ArrowRight size={18} />
          </button>
        ) : (
          <div className="best-foot">
            <ShieldCheck size={16} />
            정가와 적용 조건이 확인되면 내 가격을 계산해요.
          </div>
        )}
        {result.basePrice && (
          <a
            className="base-source"
            href={result.basePrice.source.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            공식 정가 {money(result.basePrice.amount)} · {result.basePrice.product} ·{' '}
            {result.basePrice.priceType}
            <ExternalLink size={13} />
          </a>
        )}
      </section>
      <details className="search-trace">
        <summary>
          어떤 혜택을 찾아봤나요?<span>탐색 기록 보기</span>
        </summary>
        <div>
          {result.tasks.map((t) => (
            <div className="trace-row" key={t.id}>
              <span>{categories[t.category] || t.category}</span>
              <span className={`trace-status ${t.status}`}>
                {t.status === 'complete'
                  ? `${t.found}개 후보 · ${t.sourceCount}개 페이지`
                  : t.status === 'unsupported'
                    ? '이 모드에서 미지원'
                    : '확인 실패'}
              </span>
              {t.message && <small>{t.message}</small>}
            </div>
          ))}
        </div>
      </details>
      <section className="benefits-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">MATCHED TO YOU</span>
            <h2>
              내 혜택으로 살펴본 할인<span className="count">{result.alternatives.length}</span>
            </h2>
          </div>
        </div>
        <div className="filter-tabs" role="group" aria-label="적용 상태 필터">
          {[
            ['all', '전체'],
            ['confirmed', '적용 확인됨'],
            ['needs_info', '추가 정보 필요'],
            ['not_eligible', '해당 없음'],
            ['unknown', '근거 부족'],
          ].map(([key, label]) => (
            <button
              key={key}
              className={filter === key ? 'selected' : ''}
              aria-pressed={filter === key}
              onClick={() => setFilter(key)}
            >
              {label}
            </button>
          ))}
        </div>
        {visible.length ? (
          visible.map((b) => <BenefitCard key={b.id} benefit={b} onSelect={() => setSelected(b)} />)
        ) : (
          <div className="empty-state">
            <Ticket size={25} />
            <p>
              {result.summary.found === 0
                ? '검증 가능한 할인 근거를 찾지 못했어요.'
                : '이 상태에 해당하는 혜택이 없어요.'}
            </p>
            <small>결과가 없다는 것이 할인이 없다는 뜻은 아니에요.</small>
          </div>
        )}
      </section>
      {result.opportunities.length > 0 && (
        <section className="benefits-section discovery-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">MORE POSSIBILITIES</span>
              <h2>
                함께 확인할 공개 혜택<span className="count">{result.opportunities.length}</span>
              </h2>
            </div>
            <ArrowUpRight size={23} />
          </div>
          <p className="section-description">
            내 프로필 외에 찾은 경로예요. 추가 조건을 확인한 뒤 이용하세요.
          </p>
          {result.opportunities.map((b) => (
            <BenefitCard key={b.id} benefit={b} onSelect={() => setSelected(b)} />
          ))}
        </section>
      )}
      <p className="result-disclaimer">
        현재 읽을 수 있는 공식 근거를 기준으로 안내해요. 최종 적용 여부와 결제 금액은 구매처에서
        다시 확인해주세요.
      </p>
      {selected && <BenefitDetail benefit={selected} onClose={() => setSelected(null)} />}
    </>
  );
}
function BenefitCard({
  benefit: b,
  onSelect,
}: {
  benefit: EvaluatedBenefit;
  onSelect: () => void;
}) {
  return (
    <article className={`benefit-card status-${b.eligibility.status}`}>
      <div className="benefit-icon">
        <Ticket size={23} />
      </div>
      <div className="benefit-body">
        <div className="benefit-kicker">
          <span>{b.provider}</span>
          <span className={`status ${b.eligibility.status}`}>
            {b.eligibility.status === 'confirmed' ? (
              <Check size={12} />
            ) : b.eligibility.status === 'not_eligible' ? (
              <X size={12} />
            ) : (
              <CircleHelp size={12} />
            )}
            {statusLabels[b.eligibility.status]}
          </span>
        </div>
        <h3>{b.title}</h3>
        <p className="discount-text">{discountLabel(b)}</p>
        <p className="benefit-condition">
          {b.eligibility.failed[0] ||
            b.eligibility.missing[0]?.question ||
            b.caveats[0] ||
            '상세 이용 조건을 확인해주세요.'}
        </p>
        <div className="benefit-bottom">
          <a href={b.source.url} target="_blank" rel="noopener noreferrer">
            <ShieldCheck size={13} />
            {b.source.official ? '공식 출처' : '출처'}
            <ExternalLink size={12} />
          </a>
          <button onClick={onSelect}>
            조건 자세히 보기
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
      <div className="benefit-price">
        <small>내 가격</small>
        <strong>{b.finalPrice === null ? '확인 필요' : money(b.finalPrice)}</strong>
      </div>
    </article>
  );
}
