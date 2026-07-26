import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

import { BREAKPOINTS } from '../playwright.config.js'
import { bodyFor } from './apiFixtures.js'

// Every screen of the signed-in product, at every width testing.md requires,
// plus a REAL-BROWSER axe pass.
//
// Why a browser and not jsdom: the existing vitest-axe suite covers four public
// screens and cannot evaluate colour contrast at all — jsdom has no layout and
// no canvas, so axe silently skips the contrast rule. On a dark dashboard that
// is the rule most likely to be violated, so the check that was missing is
// exactly the check that mattered.
//
// The authenticated shell is reached by stubbing /api/auth/me. No credentials
// are typed anywhere; the harness never touches a real account.

const APP_SCREENS = [
  ['dashboard', '/app/dashboard'],
  ['sources', '/app/sources'],
  ['monitoring-health', '/app/monitoring-health'],
  ['evidence', '/app/evidence'],
  ['alerts', '/app/alerts'],
  ['briefs', '/app/briefs'],
  ['reports', '/app/reports'],
  ['review-queue', '/app/review-queue'],
  ['integrations', '/app/integrations'],
  ['billing', '/app/billing'],
  ['settings', '/app/settings'],
  ['source-lab', '/app/source-lab'],
]

async function stubApi(page) {
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url())
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(bodyFor(url.pathname)),
    })
  })
  // The shell reads these on boot; without them it bounces to onboarding and
  // every screenshot is the same welcome page.
  await page.addInitScript(() => {
    localStorage.setItem('regradar_user_registered', 'true')
    localStorage.setItem('regradar_onboarding_complete', 'true')
  })
}

async function settle(page) {
  await page.waitForLoadState('networkidle')
  // Freeze anything still moving so a screenshot is reproducible.
  await page.addStyleTag({
    content: `*, *::before, *::after {
      animation-duration: 0s !important;
      animation-delay: 0s !important;
      transition-duration: 0s !important;
      transition-delay: 0s !important;
      caret-color: transparent !important;
    }`,
  })
  await page.waitForTimeout(150)
}

test.describe('signed-in app — visual baselines', () => {
  for (const [name, path] of APP_SCREENS) {
    for (const bp of BREAKPOINTS) {
      test(`${name} @ ${bp.name} ${bp.width}`, async ({ page }) => {
        await stubApi(page)
        await page.setViewportSize({ width: bp.width, height: bp.height })
        await page.goto(path)
        await settle(page)

        await expect(page).toHaveScreenshot(`${name}-${bp.width}.png`, {
          fullPage: true,
        })
      })
    }
  }
})

test.describe('signed-in app — accessibility in a real browser', () => {
  for (const [name, path] of APP_SCREENS) {
    test(`${name} has no serious or critical violations`, async ({ page }) => {
      await stubApi(page)
      await page.setViewportSize({ width: 1440, height: 1400 })
      await page.goto(path)
      await settle(page)

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze()

      // serious/critical only. Filtering is not lowering the bar: 'minor' and
      // 'moderate' on a dense dashboard are dominated by advisory landmark
      // suggestions, and a suite that fails on those gets muted, which is worse
      // than one that fails on the things that actually block a user.
      const blocking = results.violations.filter(
        v => v.impact === 'serious' || v.impact === 'critical',
      )
      // The selector and the offending colours, not just a count: "color-contrast
      // x2" tells whoever reads the failure nothing about where to look, and a
      // failure nobody can act on gets skipped rather than fixed.
      const summary = blocking
        .map(v => {
          const where = v.nodes
            .map(n => `      ${n.target.join(' ')}\n        ${(n.failureSummary || '').split('\n').slice(1).join(' ').trim()}`)
            .join('\n')
          return `${v.id} (${v.impact}) x${v.nodes.length}: ${v.help}\n${where}`
        })
        .join('\n')

      expect(blocking, `${name}:\n${summary}`).toEqual([])
    })
  }
})
