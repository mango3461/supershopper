import type { BenefitCandidate, EvaluatedBenefit } from '../../schemas';
export function deduplicate(items: BenefitCandidate[]): BenefitCandidate[] {
  const groups = new Map<string, BenefitCandidate>();
  for (const item of items) {
    const key = JSON.stringify([
      item.merchant,
      item.provider,
      item.title,
      item.context,
      [...item.requirements].sort((a, b) => a.field.localeCompare(b.field)),
    ]);
    const previous = groups.get(key);
    if (!previous) {
      groups.set(key, item);
      continue;
    }
    const preferred = item.source.official && !previous.source.official ? item : previous;
    if (
      JSON.stringify(item.discount) !== JSON.stringify(previous.discount) ||
      item.validFrom !== previous.validFrom ||
      item.validUntil !== previous.validUntil
    ) {
      groups.set(key, {
        ...preferred,
        calculationSafe: false,
        confidence: 'low',
        caveats: [
          ...new Set([
            ...previous.caveats,
            ...item.caveats,
            '출처 사이의 할인 금액 또는 기간이 일치하지 않습니다.',
          ]),
        ],
      });
    } else
      groups.set(key, {
        ...preferred,
        mode: previous.mode === 'personal' || item.mode === 'personal' ? 'personal' : 'discovery',
      });
  }
  return [...groups.values()];
}
export function rank(items: EvaluatedBenefit[]) {
  const status = { confirmed: 0, needs_info: 1, unknown: 2, not_eligible: 3 };
  const sorted = [...items].sort(
    (a, b) =>
      status[a.eligibility.status] - status[b.eligibility.status] ||
      (a.finalPrice ?? Infinity) - (b.finalPrice ?? Infinity) ||
      Number(b.source.official) - Number(a.source.official),
  );
  const best =
    sorted.find((b) => b.eligibility.status === 'confirmed' && b.finalPrice !== null) ?? null;
  return {
    best,
    alternatives: sorted.filter(
      (b) => b !== best && (b.mode === 'personal' || b.eligibility.status === 'confirmed'),
    ),
    opportunities: sorted.filter(
      (b) => b !== best && b.mode === 'discovery' && b.eligibility.status !== 'confirmed',
    ),
  };
}
