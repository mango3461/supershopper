import { z } from 'zod';

export const dateSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/)
  .refine(
    (v) => !Number.isNaN(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v,
    '유효한 날짜를 입력해주세요',
  );
const text = z.string().max(2000);
export const profileSchema = z.object({
  age: z.number().int().min(0).max(120).nullable().optional(),
  birthYear: z.number().int().min(1900).max(2100).nullable().optional(),
  location: text.nullable().optional(),
  occupation: text.nullable().optional(),
  carrier: z.object({ provider: text, grade: text.nullable().optional() }).nullable().optional(),
  cards: z.array(z.object({ issuer: text, product: text })).max(20),
  memberships: z.array(text).max(20),
});
export type UserProfile = z.infer<typeof profileSchema>;
export const intentSchema = z.object({
  merchant: z.string().min(1).max(100),
  product: text.nullable(),
  date: dateSchema.nullable(),
  location: text.nullable(),
  quantity: z.number().int().min(1).max(100).nullable(),
});
export type PurchaseIntent = z.infer<typeof intentSchema>;
export const categorySchema = z.enum([
  'card',
  'carrier',
  'membership',
  'age',
  'occupation',
  'location',
  'promotion',
]);
export const taskSchema = z.object({
  id: text,
  category: categorySchema,
  query: text,
  profileEvidence: z.array(text),
  mode: z.enum(['personal', 'discovery']),
});
export const planSchema = z.object({ tasks: z.array(taskSchema).min(1).max(8) });
export type SearchTask = z.infer<typeof taskSchema>;
export const requirementSchema = z.object({
  field: text,
  operator: z.enum(['equals', 'contains', 'gte', 'lte', 'in', 'unknown']),
  value: z.union([z.string(), z.number(), z.array(z.string())]),
  description: text,
});
export const sourceSchema = z.object({
  url: z.url().refine((v) => new URL(v).protocol === 'https:'),
  title: text,
  official: z.boolean(),
  retrievedAt: z.iso.datetime(),
  excerpt: text,
  verified: z.boolean(),
});
export const contextSchema = z.object({
  product: text.nullable(),
  priceType: text.nullable(),
  date: dateSchema.nullable(),
  channel: text.nullable(),
  quantity: z.number().int().positive().nullable(),
});
export const benefitSchema = z.object({
  id: text,
  title: text,
  merchant: text,
  provider: text,
  category: z.enum([...categorySchema.options, 'other']),
  mode: z.enum(['personal', 'discovery']),
  discount: z.object({
    type: z.enum(['percentage', 'fixed', 'special_price', 'unknown']),
    value: z.number().nonnegative().nullable(),
    specialPrice: z.number().int().nonnegative().nullable(),
    cap: z.number().int().nonnegative().nullable(),
  }),
  requirements: z.array(requirementSchema).max(30),
  validFrom: dateSchema.nullable(),
  validUntil: dateSchema.nullable(),
  purchaseMethod: text.nullable(),
  stackable: z.boolean().nullable(),
  source: sourceSchema,
  confidence: z.enum(['high', 'medium', 'low']),
  context: contextSchema,
  conditionsComplete: z.boolean(),
  calculationSafe: z.boolean(),
  caveats: z.array(text),
});
export type BenefitCandidate = z.infer<typeof benefitSchema>;
export const extractionSchema = z.object({ benefits: z.array(benefitSchema).max(10) });
export const eligibilitySchema = z.object({
  status: z.enum(['confirmed', 'needs_info', 'not_eligible', 'unknown']),
  matched: z.array(text),
  missing: z.array(z.object({ field: text, question: text })),
  failed: z.array(text),
});
export type Eligibility = z.infer<typeof eligibilitySchema>;
export const evaluatedSchema = benefitSchema.extend({
  eligibility: eligibilitySchema,
  originalPrice: z.number().nullable(),
  finalPrice: z.number().nullable(),
  savedAmount: z.number().nullable(),
});
export type EvaluatedBenefit = z.infer<typeof evaluatedSchema>;
export const basePriceSchema = contextSchema.extend({
  amount: z.number().int().positive(),
  currency: z.literal('KRW'),
  source: sourceSchema,
});
export type BasePrice = z.infer<typeof basePriceSchema>;
export const baseResolutionSchema = z.object({
  basePrice: basePriceSchema.nullable(),
  reason: text,
});
export const traceSchema = z.object({
  id: text,
  category: text,
  query: text,
  status: z.enum(['complete', 'failed', 'unsupported']),
  sourceCount: z.number(),
  found: z.number(),
  latencyMs: z.number(),
  message: text.nullable(),
});
export type TaskTrace = z.infer<typeof traceSchema>;
export const responseSchema = z.object({
  merchant: text,
  intent: intentSchema,
  basePrice: basePriceSchema.nullable(),
  basePriceReason: text,
  summary: z.object({
    searched: z.number(),
    found: z.number(),
    confirmed: z.number(),
    needsInfo: z.number(),
  }),
  best: evaluatedSchema.nullable(),
  alternatives: z.array(evaluatedSchema),
  opportunities: z.array(evaluatedSchema),
  tasks: z.array(traceSchema),
  warnings: z.array(text),
  provider: text,
  checkedAt: z.iso.datetime(),
  elapsedMs: z.number(),
});
export type SearchResponse = z.infer<typeof responseSchema>;
export const requestSchema = z.object({
  query: z.string().trim().min(1).max(300),
  profile: profileSchema.optional(),
  visitDate: dateSchema.optional(),
});
