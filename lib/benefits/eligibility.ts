import type { BenefitCandidate, Eligibility, PurchaseIntent, UserProfile } from '../../schemas';
import { isOfficial } from '../search/evidence';

export function evaluateEligibility(
  benefit: BenefitCandidate,
  profile: UserProfile,
  intent: PurchaseIntent,
  today: string,
): Eligibility {
  const matched: string[] = [];
  const failed: string[] = [];
  const missing: Eligibility['missing'] = [];
  const date = intent.date ?? today;
  if (benefit.validUntil && benefit.validUntil < date)
    failed.push('선택한 날짜에는 종료된 혜택입니다.');
  if (benefit.validFrom && benefit.validFrom > date)
    failed.push('선택한 날짜에는 시작 전인 혜택입니다.');
  const fields: Record<string, unknown> = {
    age: profile.age,
    birthYear: profile.birthYear,
    occupation: profile.occupation,
    location: profile.location,
    'carrier.provider': profile.carrier?.provider,
    'carrier.grade': profile.carrier?.grade,
    'cards.issuer': profile.cards.map((c) => c.issuer),
    'cards.product': profile.cards.map((c) => `${c.issuer} ${c.product}`),
    memberships: profile.memberships,
    date: intent.date,
    quantity: intent.quantity,
    product: intent.product,
  };
  for (const r of benefit.requirements) {
    const actual = fields[r.field];
    if (r.operator === 'unknown' || actual == null || actual === '') {
      missing.push({ field: r.field, question: r.description });
      continue;
    }
    let passes: boolean | null = null;
    if (r.operator === 'equals')
      passes = Array.isArray(actual) ? actual.includes(r.value) : actual === r.value;
    if (r.operator === 'contains')
      passes = Array.isArray(actual)
        ? actual.includes(r.value)
        : typeof actual === 'string' && actual === r.value;
    if (r.operator === 'gte' && typeof actual === 'number' && typeof r.value === 'number')
      passes = actual >= r.value;
    if (r.operator === 'lte' && typeof actual === 'number' && typeof r.value === 'number')
      passes = actual <= r.value;
    if (r.operator === 'in' && Array.isArray(r.value)) {
      const allowed = r.value;
      passes = Array.isArray(actual)
        ? actual.some((a) => allowed.includes(a))
        : allowed.includes(String(actual));
    }
    if (passes === null) missing.push({ field: r.field, question: r.description });
    else if (passes) matched.push(r.description);
    else failed.push(r.description);
  }
  if (!intent.date)
    missing.push({
      field: 'date',
      question: '언제 방문하시나요? 방문일에 유효한 혜택인지 확인해야 해요.',
    });
  let status: Eligibility['status'] = failed.length
    ? 'not_eligible'
    : missing.length
      ? 'needs_info'
      : 'confirmed';
  if (
    !failed.length &&
    (!benefit.source.verified ||
      !benefit.source.official ||
      !isOfficial(benefit.source.url) ||
      benefit.confidence === 'low')
  )
    status = 'unknown';
  if (
    status === 'confirmed' &&
    (!benefit.conditionsComplete || !benefit.validFrom || !benefit.validUntil)
  )
    status = 'unknown';
  return { status, matched, missing, failed };
}
