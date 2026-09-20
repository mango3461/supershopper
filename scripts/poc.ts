import { mkdir, writeFile } from 'node:fs/promises';
import { search } from '../lib/search/engine';
async function main() {
  const result = await search({ query: process.argv[2] || '에버랜드' });
  console.log(JSON.stringify(result, null, 2));
  await mkdir('.scratch', { recursive: true });
  await writeFile('.scratch/poc-result.json', JSON.stringify(result, null, 2));
  if (!result.summary.found) throw new Error('실제 근거가 있는 후보를 찾지 못했습니다.');
}
main().catch(() => {
  console.error('PoC 실패: 설정 또는 공식 페이지 접근 상태를 확인하세요.');
  process.exitCode = 1;
});
