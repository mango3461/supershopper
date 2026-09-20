import type {
  BasePrice,
  BenefitCandidate,
  Eligibility,
  EvaluatedBenefit,
  PurchaseIntent,
} from '../../schemas';
import { isOfficial } from '../search/evidence';
export function calculate(
  benefit: BenefitCandidate,
  eligibility: Eligibility,
  base: BasePrice | null,
  intent: PurchaseIntent,
): EvaluatedBenefit {
  const result: EvaluatedBenefit = {
    ...benefit,
    eligibility,
    originalPrice: null,
    finalPrice: null,
    savedAmount: null,
  };
  if (
    !base ||
    !base.source.verified ||
    !base.source.official ||
    !isOfficial(base.source.url) ||
    eligibility.status !== 'confirmed' ||
    !benefit.calculationSafe ||
    !intent.date ||
    !intent.product ||
    intent.quantity !== 1
  )
    return result;
  if (base.date !== intent.date || base.product !== intent.product || base.quantity !== 1)
    return result;
  if (
    ['product', 'priceType', 'date', 'channel', 'quantity'].some((key) => {
      const k = key as keyof typeof benefit.context;
      return base[k] == null || benefit.context[k] !== base[k];
    })
  )
    return result;
  const d = benefit.discount;
  let final: number | null = null;
  if (d.type === 'percentage' && d.value != null && d.value > 0 && d.value <= 100) {
    const saving = (base.amount * d.value) / 100;
    // No undocumented rounding convention: fractional won remain uncalculated.
    if (Number.isInteger(saving)) final = base.amount - Math.min(saving, d.cap ?? saving);
  }
  if (d.type === 'fixed' && d.value != null && Number.isInteger(d.value))
    final = Math.max(0, base.amount - Math.min(d.value, d.cap ?? d.value));
  if (d.type === 'special_price' && d.specialPrice != null) final = d.specialPrice;
  if (final == null || final < 0 || final > base.amount) return result;
  return {
    ...result,
    originalPrice: base.amount,
    finalPrice: final,
    savedAmount: base.amount - final,
  };
}
