// A design token nobody uses is worse than no token: the next author cannot tell
// which half of the system is real.
//
// Measured 2026-07-25: 55 tokens defined in src/index.css, 24 of them referenced
// exactly nowhere — a spacing scale that Tailwind classes had superseded, an
// easing/duration set, three status colours, and --surface-glass, a leftover from
// the pass that removed glassmorphism ("was translucent; now opaque").
//
// This guard fails the moment a new one is added without a use. That is the point:
// the choice — use it or drop it — should be made when the token is written, not
// discovered in an audit a year later.

import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'

const SRC = resolve(import.meta.dirname, '..')

function walk(dir) {
  return readdirSync(dir).flatMap(entry => {
    const full = join(dir, entry)
    return statSync(full).isDirectory() ? walk(full) : [full]
  })
}

const FILES = walk(SRC).filter(f => /\.(jsx?|tsx?|css)$/.test(f))
const CSS = readFileSync(join(SRC, 'index.css'), 'utf8')

const defined = new Set([...CSS.matchAll(/^\s*(--[a-z0-9-]+)\s*:/gm)].map(m => m[1]))

const used = new Set()
for (const file of FILES) {
  const text = readFileSync(file, 'utf8')
  // A CSS custom-property reference, in a stylesheet or an inline style, plus
  // Tailwind's arbitrary-property form.
  for (const m of text.matchAll(/var\((--[a-z0-9-]+)/g)) used.add(m[1])
  for (const m of text.matchAll(/\[(--[a-z0-9-]+)\]/g)) used.add(m[1])
}

describe('design tokens', () => {
  it('defines no token that nothing references', () => {
    const dead = [...defined].filter(token => !used.has(token)).sort()
    expect(
      dead,
      `Unused design tokens in src/index.css:\n  ${dead.join('\n  ')}\n` +
        'Use them or remove them — a half-dead token list makes the system unreadable.',
    ).toEqual([])
  })

  it('still defines the tokens the app actually reads', () => {
    const missing = [...used].filter(token => !defined.has(token)).sort()
    // A referenced-but-undefined token silently renders as nothing, which is how a
    // colour becomes transparent and a spacing becomes zero.
    expect(missing, `Referenced but never defined:\n  ${missing.join('\n  ')}`).toEqual([])
  })
})
