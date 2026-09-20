import { load } from 'cheerio';
import type { EvidencePage } from './provider';
// Only known official public hosts can be fetched. Model-generated URLs never get arbitrary network access.
export const officialDomains = [
  'everland.com',
  'hyundaicard.com',
  'samsungcard.com',
  'shinhancard.com',
  'kbcard.com',
  'hanacard.co.kr',
  'bccard.com',
  'lottecard.co.kr',
  'nhcard.co.kr',
  'tworld.co.kr',
  'kt.com',
  'lguplus.com',
  'plus.naver.com',
];
export const normalizeText = (value: string) => value.replace(/\s+/g, ' ').trim();
export function isOfficial(url: string) {
  try {
    const u = new URL(url);
    return (
      u.protocol === 'https:' &&
      !u.username &&
      !u.password &&
      (!u.port || u.port === '443') &&
      officialDomains.some((d) => u.hostname === d || u.hostname.endsWith('.' + d))
    );
  } catch {
    return false;
  }
}
export async function fetchEvidence(url: string, signal?: AbortSignal): Promise<EvidencePage> {
  if (!isOfficial(url)) throw new Error('공식 출처 허용 목록에 없는 URL입니다.');
  const timeout = AbortSignal.timeout(12000);
  const res = await fetch(url, {
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    redirect: 'manual',
    headers: { 'User-Agent': 'SuperShopper/0.1 (public benefit evidence)' },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error('공식 페이지를 읽을 수 없습니다.');
  if (!res.headers.get('content-type')?.includes('text/html'))
    throw new Error('지원하지 않는 문서 형식입니다.');
  const reader = res.body?.getReader();
  if (!reader) throw new Error('빈 문서');
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > 2_000_000) {
      await reader.cancel();
      throw new Error('문서 크기 제한');
    }
    chunks.push(value);
  }
  const html = Buffer.concat(chunks).toString('utf8');
  const $ = load(html);
  $('script,style,noscript,iframe').remove();
  return {
    url,
    title: normalizeText($('title').text()),
    html,
    text: normalizeText($('body').text()).slice(0, 65000),
    retrievedAt: new Date().toISOString(),
  };
}
