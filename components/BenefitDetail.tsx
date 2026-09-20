'use client';
import Link from 'next/link';
import { ExternalLink, ShieldCheck, CheckCircle2, CircleHelp } from 'lucide-react';
import type { EvaluatedBenefit } from '../schemas';
import { Drawer } from './Drawer';
export const statusLabels = {
  confirmed: '적용 확인됨',
  needs_info: '추가 정보 필요',
  not_eligible: '해당 없음',
  unknown: '근거 부족',
};
export const money = (n: number) => `${n.toLocaleString('ko-KR')}원`;
export function discountLabel(b: EvaluatedBenefit) {
  return b.discount.type === 'percentage' && b.discount.value != null
    ? `${b.discount.value}% 할인 안내`
    : b.discount.type === 'fixed' && b.discount.value != null
      ? `${money(b.discount.value)} 할인 안내`
      : b.discount.type === 'special_price' && b.discount.specialPrice != null
        ? `공식 특가 ${money(b.discount.specialPrice)}`
        : '상세 조건 확인';
}
export function BenefitDetail({
  benefit: b,
  onClose,
}: {
  benefit: EvaluatedBenefit;
  onClose: () => void;
}) {
  return (
    <Drawer title="혜택 자세히 보기" onClose={onClose}>
      <span className={`status ${b.eligibility.status}`}>{statusLabels[b.eligibility.status]}</span>
      <p className="detail-provider">{b.provider}</p>
      <h3 className="detail-title">{b.title}</h3>
      <div className="detail-price">
        <span>내 가격 · 예상 결제가</span>
        <strong>{b.finalPrice === null ? '아직 확정할 수 없어요' : money(b.finalPrice)}</strong>
        <small>
          {b.finalPrice === null
            ? '자격·정가·가격 조건을 모두 확인한 경우에만 계산해요.'
            : `정가 ${money(b.originalPrice!)} · ${money(b.savedAmount!)} 절약`}
        </small>
      </div>
      <section className="detail-section">
        <h4>할인 안내</h4>
        <p>{discountLabel(b)}</p>
        <p className="muted">{b.purchaseMethod || '구매 방법 확인 필요'}</p>
        {b.discount.cap != null && <p>할인 한도 {money(b.discount.cap)}</p>}
      </section>
      {b.eligibility.matched.length > 0 && (
        <section className="detail-section">
          <h4>
            <CheckCircle2 size={17} />내 프로필과 맞는 조건
          </h4>
          <ul>
            {b.eligibility.matched.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </section>
      )}
      {b.eligibility.missing.length > 0 && (
        <section className="detail-section missing-box">
          <h4>
            <CircleHelp size={17} />
            추가로 확인해주세요
          </h4>
          <ul>
            {b.eligibility.missing.map((s, i) => (
              <li key={i}>{s.question}</li>
            ))}
          </ul>
          <Link className="text-link" href="/profile">
            내 혜택 정보 수정하기 →
          </Link>
        </section>
      )}
      {b.eligibility.failed.length > 0 && (
        <section className="detail-section">
          <h4>적용되지 않는 이유</h4>
          <ul>
            {b.eligibility.failed.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </section>
      )}
      <section className="detail-section">
        <h4>기간 및 이용 조건</h4>
        <dl className="detail-facts">
          <div>
            <dt>유효기간</dt>
            <dd>
              {b.validFrom || '시작일 미확인'} ~ {b.validUntil || '종료일 미확인'}
            </dd>
          </div>
          <div>
            <dt>구매 채널</dt>
            <dd>{b.context.channel || '확인 필요'}</dd>
          </div>
          <div>
            <dt>중복 할인</dt>
            <dd>
              {b.stackable === null ? '확인되지 않음' : b.stackable ? '가능 (조건 확인)' : '불가'}
            </dd>
          </div>
        </dl>
        <ul>
          {b.caveats.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </section>
      <section className="detail-section">
        <h4>
          <ShieldCheck size={17} />
          {b.source.official ? '공식 출처' : '출처'}
        </h4>
        <a className="source-title" href={b.source.url} target="_blank" rel="noopener noreferrer">
          {b.source.title}
          <ExternalLink size={14} />
        </a>
        <p className="source-host">{new URL(b.source.url).hostname}</p>
        <blockquote>{b.source.excerpt}</blockquote>
        <small className="muted">
          본문 확인:{' '}
          {new Date(b.source.retrievedAt).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })} (한국
          시간)
        </small>
      </section>
      <a
        className="primary-button detail-cta"
        href={b.source.url}
        target="_blank"
        rel="noopener noreferrer"
      >
        공식 페이지에서 조건 확인
        <ExternalLink size={18} />
      </a>
    </Drawer>
  );
}
