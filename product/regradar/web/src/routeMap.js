const PUBLIC_VIEW_PATHS = {
  landing: '/',
  login: '/login',
  register: '/register',
  pricing: '/pricing',
  'source-readiness-review': '/source-readiness-review',
  terms: '/terms',
  privacy: '/privacy',
  disclaimer: '/disclaimer',
  'choose-plan': '/app/choose-plan',
}

const APP_PAGE_PATHS = {
  dashboard: '/app/dashboard',
  sources: '/app/sources',
  'source-lab': '/app/source-lab',
  evidence: '/app/evidence',
  alerts: '/app/alerts',
  briefs: '/app/briefs',
  reports: '/app/reports',
  integrations: '/app/integrations',
  billing: '/app/billing',
  settings: '/app/settings',
}

const PATH_APP_PAGES = Object.fromEntries(
  Object.entries(APP_PAGE_PATHS).map(([page, path]) => [path, page]),
)

const PATH_PUBLIC_VIEWS = Object.fromEntries(
  Object.entries(PUBLIC_VIEW_PATHS).map(([view, path]) => [path, view]),
)

function normalizePath(pathname = '/') {
  const path = String(pathname || '/').split('?')[0].split('#')[0]
  if (path.length > 1 && path.endsWith('/')) return path.slice(0, -1)
  return path || '/'
}

export function pathToRoute(pathname = '/') {
  const path = normalizePath(pathname)
  if (path === '/app' || path === '/app/') {
    return { view: 'app', appPage: 'dashboard' }
  }
  if (path === '/app/sources/new') {
    return { view: 'app', appPage: 'source-lab' }
  }
  if (PATH_APP_PAGES[path]) {
    return { view: 'app', appPage: PATH_APP_PAGES[path] }
  }
  if (PATH_PUBLIC_VIEWS[path]) {
    return { view: PATH_PUBLIC_VIEWS[path], appPage: 'dashboard' }
  }
  return { view: 'landing', appPage: 'dashboard' }
}

export function publicViewToPath(view) {
  return PUBLIC_VIEW_PATHS[view] || '/'
}

export function appPageToPath(page) {
  return APP_PAGE_PATHS[page] || APP_PAGE_PATHS.dashboard
}
