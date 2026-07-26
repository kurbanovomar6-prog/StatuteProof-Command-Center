import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

import { BREAKPOINTS } from '../playwright.config.js'
import { bodyFor } from './apiFixtures.js'

// The public site: everything a buyer sees before they have an account.
//
// The signed-in product got a browser harness first because it was the part
// nobody could look at. But the public pages are where the buying decision
// happens, and they had exactly four screens under a jsdom axe run that cannot
// evaluate colour contrast. These are the same four widths and the same
// real-browser axe pass.
//
// Signed OUT on purpose: /api/auth/me returns 401 so the landing, pricing and
// legal pages render the way a first-time visitor actually sees them. Rendering
// them with a session would screenshot a state no prospect ever reaches.

const PUBLIC_SCREENS = [
  ['landing', '/'],
  ['pricing', '/pricing'],
  ['login', '/login'],
  ['register', '/register'],
  ['forgot-password', '/forgot-password'],
  // Both were uncovered. reset-password especially: it renders the surface this
  // work rebuilt, and an untested page is where the next regression lands.
  ['reset-password', '/reset-password'],
  ['verify-email', '/verify-email'],
  ['source-readiness-review', '/source-readiness-review'],
  ['verify', '/verify'],
  ['terms', '/terms'],
  ['privacy', '/privacy'],
  ['disclaimer', '/disclaimer'],
  ['room', '/room/sample-share-token'],
]

async function stubSignedOut(page) {
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname.startsWith('/api/auth/me') || url.pathname.startsWith('/api/profile')) {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ ok: false, error: 'unauthenticated' }),
      })
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(bodyFor(url.pathname)),
    })
  })
  await page.addInitScript(() => {
    localStorage.clear()
  })
}

async function settle(page) {
  await page.waitForLoadState('networkidle')
  await page.addStyleTag({
    content: `*, *::before, *::after {
      animation-duration: 0s !important;
      animation-delay: 0s !important;
      transition-duration: 0s !important;
      transition-delay: 0s !important;
      caret-color: transparent !important;
    }`,
  })
  // Scroll-triggered reveals leave content invisible in a screenshot taken at
  // the top of a long marketing page, so force anything reveal-gated on.
  await page.evaluate(() => {
    document.querySelectorAll('[class*="opacity-0"], [data-reveal]').forEach(el => {
      el.style.opacity = '1'
      el.style.transform = 'none'
    })
  })
  await page.waitForTimeout(150)
}

test.describe('public site — visual baselines', () => {
  for (const [name, path] of PUBLIC_SCREENS) {
    for (const bp of BREAKPOINTS) {
      test(`${name} @ ${bp.name} ${bp.width}`, async ({ page }) => {
        await stubSignedOut(page)
        await page.setViewportSize({ width: bp.width, height: bp.height })
        await page.goto(path)
        await settle(page)

        await expect(page).toHaveScreenshot(`public-${name}-${bp.width}.png`, {
          fullPage: true,
        })
      })
    }
  }
})

test.describe('public site — accessibility in a real browser', () => {
  for (const [name, path] of PUBLIC_SCREENS) {
    test(`${name} has no serious or critical violations`, async ({ page }) => {
      await stubSignedOut(page)
      await page.setViewportSize({ width: 1440, height: 1400 })
      await page.goto(path)
      await settle(page)

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze()

      const blocking = results.violations.filter(
        v => v.impact === 'serious' || v.impact === 'critical',
      )
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

test.describe('public site — no horizontal scroll at any width', () => {
  // web/testing.md requires "verify no overflow" at every breakpoint. A marketing
  // page that scrolls sideways on a 320px phone is the most common and most
  // visible responsive defect, and no test in the repo looked for it.
  for (const [name, path] of PUBLIC_SCREENS) {
    test(`${name} fits its viewport`, async ({ page }) => {
      await stubSignedOut(page)
      for (const bp of BREAKPOINTS) {
        await page.setViewportSize({ width: bp.width, height: bp.height })
        await page.goto(path)
        await settle(page)
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
        )
        expect(overflow, `${name} overflows by ${overflow}px at ${bp.width}`)
          .toBeLessThanOrEqual(1)
      }
    })
  }
})
