import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';
const channel =
  process.env.PLAYWRIGHT_CHANNEL ||
  (process.platform === 'win32' &&
  existsSync('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
    ? 'msedge'
    : undefined);
export default defineConfig({
  testDir: './e2e',
  timeout: 45000,
  fullyParallel: false,
  workers: 1,
  use: { channel, baseURL: 'http://127.0.0.1:3000', trace: 'retain-on-failure' },
  webServer: {
    command: 'npm run start -- --hostname 127.0.0.1',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
  },
});
