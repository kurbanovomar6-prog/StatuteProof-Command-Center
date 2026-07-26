import { defineConfig, devices } from '@playwright/test'

// The visual-regression and browser-a11y harness web/testing.md has always
// required and the repo never had. It runs against the PRODUCTION BUILD served
// by `vite preview`, not the dev server: HMR injects its own client and dev-only
// warnings, so a dev-server screenshot is not a picture of what ships.
//
// The four widths are the ones testing.md names. They are declared here rather
// than inside a spec so a reader can see the contract without reading test code.
export const BREAKPOINTS = [
  { name: 'mobile', width: 320, height: 900 },
  { name: 'tablet', width: 768, height: 1200 },
  { name: 'laptop', width: 1024, height: 1200 },
  { name: 'desktop', width: 1440, height: 1400 },
]

export default defineConfig({
  testDir: './e2e',
  // Screenshots must be byte-comparable, so nothing may be racing: one worker,
  // no retries, animations frozen at their end state by the spec.
  workers: 1,
  retries: 0,
  reporter: [['list']],
  timeout: 60_000,
  expect: {
    toHaveScreenshot: {
      // An ABSOLUTE budget, not a ratio. A 1% ratio on a 1440x1400 page is
      // ~20,000 pixels — more than a rewritten paragraph — so a reworded
      // headline passed as "unchanged" and the baseline was never updated. A
      // harness that cannot see a changed sentence is not catching regressions.
      //
      // 400px absorbs glyph antialiasing across machines while still failing on
      // any real copy or layout change.
      maxDiffPixels: 400,
      animations: 'disabled',
    },
  },
  use: {
    baseURL: 'http://localhost:4173',
    ...devices['Desktop Chrome'],
    // Deterministic rendering across runs.
    colorScheme: 'dark',
    timezoneId: 'Asia/Dubai',
    locale: 'en-AE',
  },
  webServer: {
    command: 'npm run preview -- --port 4173 --strictPort',
    url: 'http://localhost:4173',
    reuseExistingServer: true,
    timeout: 120_000,
  },
})
