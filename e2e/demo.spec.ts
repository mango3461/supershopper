import { expect, test } from '@playwright/test';

test('empty evidence result is explained without inventing a price', async ({ page }) => {
  await page.route('**/api/search', (route) =>
    route.fulfill({
      json: {
        merchant: '에버랜드',
        intent: { merchant: '에버랜드', product: null, date: null, location: null, quantity: null },
        basePrice: null,
        basePriceReason: '공식 정가를 확인하지 못했어요.',
        summary: { searched: 1, found: 0, confirmed: 0, needsInfo: 0 },
        best: null,
        alternatives: [],
        opportunities: [],
        tasks: [],
        warnings: [],
        provider: 'test-only-empty-response',
        checkedAt: '2026-09-20T00:00:00.000Z',
        elapsedMs: 1,
      },
    }),
  );
  await page.goto('/search?q=에버랜드');
  await expect(page.getByText('검증 가능한 할인 근거를 찾지 못했어요.')).toBeVisible();
  await expect(page.locator('.best-card')).toContainText('— 원');
  await expect(page.locator('.benefit-card')).toHaveCount(0);
});
test('desktop: live official search, evidence drawer and profile persistence', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('정가는 같아도');
  await page.screenshot({ path: '.scratch/desktop-home.png', fullPage: true });
  await page.getByRole('textbox', { name: '어디에서 결제하시나요?' }).fill('에버랜드');
  await page.getByRole('button', { name: '내 가격 찾기', exact: true }).click();
  await expect(page.getByText('아직 확인이 필요해요', { exact: false })).toBeVisible({
    timeout: 30000,
  });
  await expect(page.locator('.benefit-card').first()).toBeVisible();
  await expect(page.locator('.best-card')).toContainText('— 원');
  await page.getByRole('button', { name: '조건 자세히 보기' }).first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('link', { name: '공식 페이지에서 조건 확인' })).toHaveAttribute(
    'href',
    /^https:\/\/reservation\.everland\.com/,
  );
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await page.screenshot({ path: '.scratch/desktop-results.png', fullPage: true });
  await page.goto('/profile');
  await page.getByLabel('멤버십 등급', { exact: true }).fill('VIP');
  await page.getByLabel('보유한 멤버십').fill('네이버플러스, 쿠팡 와우');
  await page.getByRole('button', { name: '내 혜택 저장' }).click();
  await expect(page.getByRole('status')).toContainText('저장했어요');
  await page.reload();
  await expect(page.getByLabel('멤버십 등급', { exact: true })).toHaveValue('VIP');
  await expect(page.getByLabel('보유한 멤버십')).toHaveValue('네이버플러스, 쿠팡 와우');
  expect(errors).toEqual([]);
});
test('mobile: no overflow, bottom sheets, filters and visit date', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.screenshot({ path: '.scratch/mobile-home.png', fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.goto('/search?q=에버랜드');
  await expect(page.locator('.benefit-card').first()).toBeVisible({ timeout: 30000 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: '내 혜택 보기' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: '닫기' }).click();
  await page.getByRole('button', { name: '조건 자세히 보기' }).first().click();
  const box = await page.getByRole('dialog').boundingBox();
  expect(box!.width).toBe(390);
  expect(box!.y).toBeGreaterThan(0);
  await page.screenshot({ path: '.scratch/mobile-detail.png', fullPage: true });
  await page.getByRole('button', { name: '닫기' }).click();
  await page.getByRole('button', { name: '적용 확인됨', exact: true }).click();
  await expect(page.getByText('이 상태에 해당하는 혜택이 없어요.')).toBeVisible();
  await page.getByRole('button', { name: '전체', exact: true }).click();
  await page.getByLabel('방문일', { exact: true }).fill('2026-09-25');
  await expect(page.locator('.best-card')).toContainText('정가 페이지', { timeout: 30000 });
  await page.screenshot({ path: '.scratch/mobile-results.png', fullPage: true });
});
test('API input errors and unsupported merchant are explicit', async ({ request }) => {
  expect((await request.post('/api/search', { data: { query: '' } })).status()).toBe(400);
  expect(
    (
      await request.post('/api/search', { data: { query: '에버랜드', visitDate: '2026-02-30' } })
    ).status(),
  ).toBe(400);
  expect((await request.post('/api/search', { data: { query: 'CGV' } })).status()).toBe(422);
  expect(
    (
      await request.post('/api/search', { data: { query: '에버랜드', profile: { age: -1 } } })
    ).status(),
  ).toBe(400);
  expect(
    (
      await request.post('/api/search', {
        data: '{bad',
        headers: { 'Content-Type': 'application/json' },
      })
    ).status(),
  ).toBe(400);
});
test('search failure is actionable and does not show invented results', async ({ page }) => {
  await page.route('**/api/search', (route) =>
    route.fulfill({
      status: 504,
      json: { error: { code: 'TIMEOUT', message: '검색 시간이 초과되었어요. 다시 시도해주세요.' } },
    }),
  );
  await page.goto('/search?q=에버랜드');
  await expect(page.locator('.error-state[role="alert"]')).toContainText('시간이 초과');
  await expect(page.getByRole('button', { name: '다시 검색하기' })).toBeVisible();
  await expect(page.locator('.benefit-card')).toHaveCount(0);
});
