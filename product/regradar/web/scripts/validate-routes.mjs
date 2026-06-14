import assert from 'node:assert/strict'

import {
  appPageToPath,
  pathToRoute,
  publicViewToPath,
} from '../src/routeMap.js'

const routeCases = [
  ['/', { view: 'landing', appPage: 'dashboard' }],
  ['/login', { view: 'login', appPage: 'dashboard' }],
  ['/register', { view: 'register', appPage: 'dashboard' }],
  ['/pricing', { view: 'pricing', appPage: 'dashboard' }],
  ['/source-readiness-review', { view: 'source-readiness-review', appPage: 'dashboard' }],
  ['/terms', { view: 'terms', appPage: 'dashboard' }],
  ['/privacy', { view: 'privacy', appPage: 'dashboard' }],
  ['/disclaimer', { view: 'disclaimer', appPage: 'dashboard' }],
  ['/app/choose-plan', { view: 'choose-plan', appPage: 'dashboard' }],
  ['/app/dashboard', { view: 'app', appPage: 'dashboard' }],
  ['/app/sources', { view: 'app', appPage: 'sources' }],
  ['/app/source-lab', { view: 'app', appPage: 'source-lab' }],
  ['/app/evidence', { view: 'app', appPage: 'evidence' }],
  ['/app/billing', { view: 'app', appPage: 'billing' }],
  ['/app/settings', { view: 'app', appPage: 'settings' }],
]

for (const [path, expected] of routeCases) {
  assert.deepEqual(pathToRoute(path), expected, `route mapping for ${path}`)
}

assert.equal(publicViewToPath('landing'), '/')
assert.equal(publicViewToPath('login'), '/login')
assert.equal(publicViewToPath('register'), '/register')
assert.equal(publicViewToPath('pricing'), '/pricing')
assert.equal(publicViewToPath('source-readiness-review'), '/source-readiness-review')
assert.equal(publicViewToPath('terms'), '/terms')
assert.equal(publicViewToPath('privacy'), '/privacy')
assert.equal(publicViewToPath('disclaimer'), '/disclaimer')
assert.equal(publicViewToPath('choose-plan'), '/app/choose-plan')

assert.equal(appPageToPath('dashboard'), '/app/dashboard')
assert.equal(appPageToPath('sources'), '/app/sources')
assert.equal(appPageToPath('source-lab'), '/app/source-lab')
assert.equal(appPageToPath('evidence'), '/app/evidence')
assert.equal(appPageToPath('billing'), '/app/billing')
assert.equal(appPageToPath('settings'), '/app/settings')

console.log('route mappings ok')
