import { NextResponse } from 'next/server';
import { ZodError } from 'zod';
import { createProvider, search } from '../../../lib/search/engine';
import { requestSchema } from '../../../schemas';
import { safeFailure } from '../../../lib/ai/audit';
export const runtime = 'nodejs';
export const maxDuration = 180;
let inFlight = 0;
function error(code: string, message: string, status: number) {
  return NextResponse.json(
    { error: { code, message } },
    { status, headers: { 'Cache-Control': 'no-store' } },
  );
}
export async function POST(request: Request) {
  if (inFlight >= 3) return error('BUSY', '검색 요청이 많아요. 잠시 후 다시 시도해주세요.', 429);
  if (!request.headers.get('content-type')?.includes('application/json'))
    return error('INVALID_REQUEST', 'JSON 형식으로 요청해주세요.', 415);
  inFlight++;
  try {
    const reader = request.body?.getReader();
    if (!reader) return error('INVALID_REQUEST', '검색어를 입력해주세요.', 400);
    const chunks: Uint8Array[] = [];
    let size = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > 16384) {
        await reader.cancel();
        return error('TOO_LARGE', '입력 내용이 너무 길어요.', 413);
      }
      chunks.push(value);
    }
    let json: unknown;
    try {
      json = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    } catch {
      return error('INVALID_REQUEST', '올바른 JSON을 입력해주세요.', 400);
    }
    const parsed = requestSchema.safeParse(json);
    if (!parsed.success)
      return error('INVALID_REQUEST', '검색어, 날짜, 프로필 입력을 확인해주세요.', 400);
    const signal = AbortSignal.any([request.signal, AbortSignal.timeout(150000)]);
    const result = await search(parsed.data, createProvider(signal));
    return NextResponse.json(result, { headers: { 'Cache-Control': 'no-store' } });
  } catch (e) {
    const upstream = safeFailure(e);
    if (upstream.httpStatus === 429) {
      return upstream.limitReason === 'quota_or_billing' ||
        upstream.errorCode === 'insufficient_quota'
        ? error(
            'OPENAI_QUOTA_EXCEEDED',
            '웹 검색 서비스의 API 사용 한도 또는 결제 설정을 확인해야 해요. 운영자 확인 후 다시 시도해주세요.',
            503,
          )
        : error(
            'UPSTREAM_RATE_LIMIT',
            '웹 검색 서비스의 요청 한도에 도달했어요. 잠시 후 다시 시도해주세요.',
            429,
          );
    }
    const code = e instanceof Error ? e.message : '';
    if (code === 'LIMITED_QUERY')
      return error(
        code,
        '현재는 에버랜드 공식 페이지 탐색을 지원해요. “에버랜드”로 검색하고 방문일을 선택해주세요. 자연어·다른 장소 검색은 웹 검색 모드 설정이 필요합니다.',
        422,
      );
    if (code === 'OPENAI_NOT_CONFIGURED' || code === 'GEMINI_NOT_CONFIGURED' || code === 'UNKNOWN_PROVIDER')
      return error('NOT_CONFIGURED', '검색 서비스 설정을 확인해주세요.', 503);
    if (e instanceof ZodError)
      return error(
        'INVALID_MODEL_OUTPUT',
        '검색 응답을 검증하지 못했어요. 잠시 후 다시 시도해주세요.',
        502,
      );
    if (request.signal.aborted || (e instanceof Error && /abort|timeout/i.test(e.name)))
      return error('TIMEOUT', '검색 시간이 초과되었어요. 다시 시도해주세요.', 504);
    return error('SEARCH_FAILED', '검색 연결에 실패했어요. 잠시 후 다시 시도해주세요.', 502);
  } finally {
    inFlight--;
  }
}
