import type { z } from 'zod';
import type {
  baseResolutionSchema,
  BenefitCandidate,
  PurchaseIntent,
  SearchTask,
  UserProfile,
} from '../../schemas';
export type EvidencePage = {
  url: string;
  title: string;
  text: string;
  html: string;
  retrievedAt: string;
};
export type TaskResult = {
  benefits: BenefitCandidate[];
  sourceCount: number;
  unsupported?: boolean;
  message?: string;
};
export interface SearchProvider {
  readonly name: string;
  parseIntent(query: string, today: string): Promise<PurchaseIntent>;
  planSearch(intent: PurchaseIntent, profile: UserProfile, today: string): Promise<SearchTask[]>;
  search(task: SearchTask, intent: PurchaseIntent, today: string): Promise<TaskResult>;
  resolveBasePrice(
    intent: PurchaseIntent,
    profile: UserProfile,
    today: string,
  ): Promise<z.infer<typeof baseResolutionSchema>>;
}
export function todayKorea() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date());
}
export async function mapConcurrent<T, R>(
  items: T[],
  limit: number,
  run: (item: T) => Promise<R>,
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(limit, items.length) }, async () => {
      while (next < items.length) {
        const index = next++;
        results[index] = await run(items[index]);
      }
    }),
  );
  return results;
}
