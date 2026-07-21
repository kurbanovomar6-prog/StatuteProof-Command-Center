// Honesty drift guard for the public landing surfaces (audit 2026-07-20,
// evidence_integrity + frontend_ux HIGHs):
//   - index.html meta description must not name CBUAE: commit c11c476 removed
//     CBUAE from the hero on purpose (rulebook.centralbank.ae 403s production
//     egress), so the meta description may not keep selling it.
//   - App.jsx / TrustLayer.jsx must not carry the UNCONDITIONAL present-tense
//     RFC 3161 claims ("chain head is anchored", "token ships in your evidence
//     exports") — app/rfc3161_anchor.py is dormant unless RFC3161_TSA_URL is
//     set, so the claims must be conditional ("supports ... when enabled").
//   - No public surface may name CBUAE inside a monitoring-SCOPE sentence
//     (Pricing.jsx, mockData.js, index.html): OnboardingPage.jsx and
//     Coverage.jsx disclose 0 fresh-alert-eligible CBUAE sources. Honest
//     remediation/limitation DISCLOSURES stay allowed — only scope claims fail.
//   - The /verify CHANGED sample must be described as a captured text
//     difference between two runs, not as a regulatory amendment.
//   - Cheap forbidden-claims sweep over the highest-traffic public files.
import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'

function findFile(rels) {
  const path = rels.map(r => resolve(process.cwd(), r)).find(existsSync)
  if (!path) throw new Error(`not found; looked in: ${rels.join(', ')}`)
  return path
}

const indexHtml = readFileSync(findFile(['index.html', 'web/index.html']), 'utf8')
const heroSrc = readFileSync(
  findFile(['src/components/Hero.jsx', 'web/src/components/Hero.jsx']),
  'utf8',
)
const appSrc = readFileSync(findFile(['src/App.jsx', 'web/src/App.jsx']), 'utf8')
const trustLayerSrc = readFileSync(
  findFile(['src/components/TrustLayer.jsx', 'web/src/components/TrustLayer.jsx']),
  'utf8',
)
const verifyPageSrc = readFileSync(
  findFile(['src/components/VerifyPage.jsx', 'web/src/components/VerifyPage.jsx']),
  'utf8',
)
const pricingSrc = readFileSync(
  findFile(['src/components/Pricing.jsx', 'web/src/components/Pricing.jsx']),
  'utf8',
)
const mockDataSrc = readFileSync(findFile(['src/data/mockData.js', 'web/src/data/mockData.js']), 'utf8')

// Public marketing surfaces the router renders besides the hero: App.jsx lazy-
// loads PricingPage and HowItWorks, and the rest are landing sections. The
// delivery-channel guard must read them too — the claim is just as false on
// /pricing as it is in the hero.
const PUBLIC_COPY_FILES = [
  'PricingPage.jsx',
  'HowItWorks.jsx',
  'Coverage.jsx',
  'Footer.jsx',
  'SampleBrief.jsx',
  'BuyerSourcePacks.jsx',
  'WithoutWith.jsx',
  'Problem.jsx',
  // New landing blocks (audit 2026-07-21 build): enforcement reality, honest
  // category comparison, consolidated FAQ / vendor-DD, in-page verifier. Each
  // is a customer-facing surface, so the delivery-channel + forbidden-claims
  // guards must read it too.
  'EnforcementReality.jsx',
  'Comparison.jsx',
  'FaqSection.jsx',
  'InlineVerify.jsx',
].map(name => [
  name,
  readFileSync(findFile([`src/components/${name}`, `web/src/components/${name}`]), 'utf8'),
])

// Strip JS comments: Hero.jsx legitimately mentions CBUAE ONLY in the comment
// explaining why it is excluded from the strip — that must not trip the guard.
function stripComments(src) {
  return src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|\s)\/\/.*$/gm, '$1')
}

// Collapse whitespace so JSX line wraps can't hide a phrase from a regex.
function flat(src) {
  return src.replace(/\s+/g, ' ')
}

// Comments-stripped, whitespace-collapsed source: what a reader actually sees.
function copyOf(src) {
  return flat(stripComments(src))
}

// Rough sentence split so a guard can judge one claim at a time: a limitation
// disclosed in one sentence must not excuse a scope claim in the next.
function sentences(src) {
  return copyOf(src)
    .split(/(?<=[.!?])\s+/)
    .filter(Boolean)
}

describe('index.html never claims CBUAE monitoring (hero honesty, c11c476)', () => {
  it('contains no CBUAE mention anywhere', () => {
    expect(indexHtml).not.toMatch(/CBUAE/i)
  })
})

describe('Hero.jsx claims no CBUAE outside comments', () => {
  it('code (comments stripped) contains no CBUAE', () => {
    expect(stripComments(heroSrc)).not.toMatch(/CBUAE/i)
  })
})

describe('RFC 3161 claims stay conditional (anchor is dormant-by-default)', () => {
  // Shape-based, not phrase-based: any present-tense assertion that anchoring
  // already happens fails unless the same sentence carries the "only when
  // enabled" qualifier that app/rfc3161_anchor.py actually requires.
  const UNCONDITIONAL = [
    /\b(is|are|gets?|get)\s+(automatically\s+)?anchored\b/i,
    /\b(is|are)\s+(RFC ?3161[- ])?timestamped\b/i,
    /\btokens?\s+ships?\b/i,
    /\b(every|each|all)\b[^.]{0,80}\b(includes?|ships? with|carries|contains?)\s+(an?\s+)?(RFC ?3161|timestamp token|\.tsr)/i,
  ]
  const CONDITIONAL = /\b(when|once|if)\s+(it is |they are )?(enabled|configured|switched on)|\bsupports?\b|\bcan be\b|\boptional\b/i
  const files = [
    ['App.jsx', appSrc],
    ['TrustLayer.jsx', trustLayerSrc],
  ]
  for (const [name, src] of files) {
    it(`${name} states no unconditional RFC 3161 anchoring claim`, () => {
      const offenders = sentences(src).filter(
        s => UNCONDITIONAL.some(re => re.test(s)) && !CONDITIONAL.test(s),
      )
      expect(offenders, `${name} unconditional anchoring claim(s)`).toEqual([])
    })
  }
})

// A monitoring-SCOPE sentence sells what we watch. CBUAE may only appear on a
// public surface as a disclosed limitation, never inside a scope claim.
const SCOPE_CLAIM = [
  /monitoring scope/i,
  /(regulatory |official )?sources?[^.]{0,40}\bacross\b/i,
  /source pack across/i,
  /checked on a defined schedule/i,
  /\bwe monitor\b/i,
]
const LIMITATION = /remediation|not counted|not currently counted|blocked|403|geo-?restricted|geo-?ip|unreachable|not (currently )?(monitored|available|eligible)|limitation|excluded/i

describe('no public surface sells CBUAE monitoring scope', () => {
  const files = [
    ['Pricing.jsx', pricingSrc],
    ['mockData.js', mockDataSrc],
    ['index.html', indexHtml],
  ]
  for (const [name, src] of files) {
    it(`${name} names CBUAE in no monitoring-scope sentence`, () => {
      const offenders = sentences(src).filter(
        s => /CBUAE/i.test(s) && SCOPE_CLAIM.some(re => re.test(s)) && !LIMITATION.test(s),
      )
      expect(offenders, `${name} CBUAE monitoring-scope claim(s)`).toEqual([])
    })
  }
})

describe('the /verify CHANGED sample is described as what it is', () => {
  it('VerifyPage.jsx does not call the sample a change the monitor captured', () => {
    expect(copyOf(verifyPageSrc)).not.toMatch(
      /is a change\s+(our|the)\s+monitor\s+captured|captured a (regulatory )?(change|amendment) (on|to) the official/i,
    )
  })
  it('VerifyPage.jsx discloses extraction variance between consecutive runs', () => {
    expect(copyOf(verifyPageSrc)).toMatch(/extraction variance/i)
  })
  it('VerifyPage.jsx names the sealed diff as the authoritative change count', () => {
    expect(copyOf(verifyPageSrc)).toMatch(/sealed diff[^.]{0,120}authoritative/i)
  })
})

// Delivery-channel honesty: app/alert_routing.py refuses per-customer alert
// delivery with "Telegram not connected." and app/digest_cadence.py returns
// telegram_not_connected, so a linked Telegram chat is REQUIRED for alerts
// today. Email carries account mail (verification / password reset) and the
// weekly brief, and only when STATUTEPROOF_EMAIL_SEND_ENABLED is switched on
// by us. So no public surface may sell email-delivered alerts or an optional
// Telegram. The guard is pattern-based and self-disarming: if the code stops
// hard-requiring Telegram, it stops asserting.
const alertRoutingPath = [
  '../app/alert_routing.py',
  'product/regradar/app/alert_routing.py',
]
  .map(r => resolve(process.cwd(), r))
  .find(existsSync)
const telegramRequiredForAlerts =
  Boolean(alertRoutingPath) &&
  /Telegram not connected/i.test(readFileSync(alertRoutingPath, 'utf8'))

// Fold homoglyphs and decorative punctuation to ASCII so a Cyrillic "е" or an
// em dash cannot smuggle a claim past the patterns.
const HOMOGLYPHS = {
  а: 'a', в: 'b', с: 'c', е: 'e', н: 'h', і: 'i', ј: 'j', к: 'k', м: 'm',
  о: 'o', р: 'p', ѕ: 's', т: 't', у: 'y', х: 'x',
  // Greek
  α: 'a', β: 'b', ε: 'e', η: 'h', ι: 'i', κ: 'k', μ: 'm', ν: 'v', ο: 'o',
  ρ: 'p', τ: 't', υ: 'y', χ: 'x', ζ: 'z',
}
function normalise(text) {
  return text
    .replace(/[\u200B-\u200D\uFEFF]/g, '')
    .replace(/[\u2010-\u2015]/g, '-')
    // A question mark must not fence off the second half of a claim
    // ("Telegram? Only if you want it."), so treat it as a comma here.
    .replace(/\?/g, ',')
    .replace(/[\u0370-\u03FF\u0400-\u04FF]/g, ch => HOMOGLYPHS[ch.toLowerCase()] ?? ch)
}

// Claim shapes that are false while alerts hard-require a linked Telegram
// chat. Matched as FAMILIES (inflections, punctuation, channel choice), and
// skipped when the same neighbourhood carries a negation — an honest denial
// ("email delivery is not included") is the disclosure we want authors to
// write, so the guard must never push them to delete it.
const INVERTED = [
  // Telegram sold as a nice-to-have while the code refuses without it.
  /telegram\b[^.!]{0,40}\b(optional|opt-?in)\b/i,
  /\b(optional|opt-?in)\b[^.!]{0,40}\btelegram\b/i,
  /telegram\b[^.!]{0,40}\b(if|only if|whenever) you (want|prefer|like)\b/i,
  // Delivery framed as a free choice of channel.
  /\b(e-?mail|inbox)\b[^.!]{0,24}\bor\b[^.!]{0,24}\btelegram\b/i,
  /\btelegram\b[^.!]{0,24}\bor\b[^.!]{0,24}\b(e-?mail|inbox)\b/i,
  /\bprefer\b[^.!]{0,24}\b(e-?mail|inbox)\b/i,
  // Channel pair written with a connector instead of "or" ("Email + Telegram").
  /\b(e-?mail|inbox)\b\s*[+&/]\s*\btelegram\b/i,
  /\btelegram\b\s*[+&/]\s*\b(e-?mail|inbox)\b/i,
  // Telegram sold as one of several channels while it is the only one.
  /\btelegram\b[^.!]{0,40}\b(one of|among|several|multiple)\b[^.!]{0,30}\b(delivery\s+)?(options?|channels?|methods?)\b/i,
  // Email sold as a delivery channel that is on by default.
  /\be-?mail\b[^.!]{0,30}\b(included|standard|built-?in|by default|out of the box)\b/i,
  // Email sold as the channel alerts actually arrive on.
  /\balerts?\b[^.!]{0,40}\b(delivered|sent|arrives?|arriving|lands?|reach(es)?|go(es)?|pushed?)\b[^.!]{0,40}(\b(by|via|in|to|over)\s+)?(your\s+)?\b(e-?mail|inbox|mailbox)\b/i,
  /\balerts?\b[^.!]{0,40}\be-?mailed\b/i,
  /\b(get|receive)\b[^.!]{0,30}\balerts?\b[^.!]{0,24}\b(by|via|over|in)\s+(your\s+)?(e-?mail|inbox|mailbox)\b/i,
  // Verb-first phrasing ("we email you every alert") walks past the patterns
  // above, which all require the noun "alerts" before the verb.
  /\be-?mails?\b\s+(you|your team|customers?|users?|clients?)\b[^.!]{0,30}\balerts?\b/i,
]

// Downplaying Telegram is false in either polarity, so these skip the
// negation escape: "Telegram is not required" is exactly the inverted claim.
const TELEGRAM_DOWNPLAY =
  /telegram\b[^.!]{0,40}\b(not required|isn'?t required|not needed|not necessary|not mandatory|isn'?t mandatory|not compulsory|nice[- ]to[- ]have|nice extra|bonus|add-?on)\b/i

// A denial of THIS claim, not "a negation somewhere nearby".
//
// The escape exists so an honest denial ("email delivery is not included",
// "alerts are not delivered by email") is never punished. Both a proximity
// window and an inside-the-span rule fail-open, because the span runs from the
// claim's subject to its channel and any incidental negation in that gap
// disarmed the guard ("Alerts, no chat app required, are delivered to your
// inbox." shipped green).
//
// So the escape now reasons about POLARITY: a negation only cancels the claim
// when it directly negates the claim's VERB — negation, then at most a few
// auxiliary/adverb fillers, then the verb. Everything else ("no chat app
// required, are delivered", "with no delay are delivered", "you never miss are
// emailed", "delivered — no Telegram — to your inbox") negates some other
// word while the affirmative delivery claim survives, so the guard still
// trips. The rule is deliberately fail-CLOSED: an honest sentence that trips
// can be rewritten to the disclosed shape ("Alerts are delivered to Telegram —
// a linked chat is required."), whereas a false one that passes ships.
const NEGATION_TOKEN = `(?:not|never|no|nor|isn'?t|aren'?t|doesn'?t|don'?t|cannot|can'?t|without)`
// Words allowed to sit between the negation and the verb it negates. Kept
// tight on purpose: any content word here means the negation is negating that
// word, not the delivery.
const DENIAL_FILLER = `(?:\\s+(?:be|being|been|get|gets|getting|currently|automatically|yet|ever|actually|today|normally|usually|it|they|we|you)\\b)*`
// Verb forms the claim families assert. Nouns ("delivery", "delay") are
// excluded so "No delivery delays — alerts are emailed to you." cannot pose as
// a denial.
const CLAIM_VERB = `(?:deliver|delivers|delivered|delivering|sent|send|sends|sending|arrive|arrives|arriving|land|lands|landing|reach|reaches|reaching|go|goes|going|push|pushed|pushes|e-?mail|e-?mails|e-?mailed|e-?mailing|include|includes|included|offer|offered|support|supported|available|required)`
const DENIES_CLAIM = new RegExp(
  `\\b${NEGATION_TOKEN}\\b${DENIAL_FILLER}\\s+${CLAIM_VERB}\\b`,
  'i',
)
// How much text before the match may carry the denial ("We do not email you
// alerts." — the negation precedes the span the pattern anchors on).
const DENIAL_LOOKBEHIND = 24

// Spans the delivery guard judges, one claim at a time. normalise() runs
// BEFORE the split: it folds '?' to ',' precisely so a question mark cannot
// fence off the second half of a claim, which only works if the splitter never
// sees the '?' ("<p>Telegram? Only if you want it.</p>" used to split into two
// harmless fragments and the file guard stayed silent).
function claimSpans(src) {
  return normalise(copyOf(src))
    .split(/(?<=[.!])\s+/)
    .filter(Boolean)
}

function claimsInvertedDelivery(sentence) {
  const s = normalise(sentence)
  if (TELEGRAM_DOWNPLAY.test(s)) return true
  return INVERTED.some(re => {
    const m = re.exec(s)
    if (!m) return false
    const from = Math.max(0, m.index - DENIAL_LOOKBEHIND)
    return !DENIES_CLAIM.test(s.slice(from, m.index + m[0].length))
  })
}

// The file-level pipeline. Kept as one function so the guard-of-the-guard
// probes below exercise exactly what the guarded files are read through — a
// unit probe that passes while the file pipeline stays silent is worse than
// no probe, because it certifies the surface as checked.
function deliveryOffenders(src) {
  return claimSpans(src).filter(claimsInvertedDelivery)
}

describe('delivery-channel claims match the shipped alert path', () => {
  const files = [
    ['index.html', indexHtml],
    ['Hero.jsx', heroSrc],
    ['App.jsx', appSrc],
    ['TrustLayer.jsx', trustLayerSrc],
    ['VerifyPage.jsx', verifyPageSrc],
    ['Pricing.jsx', pricingSrc],
    ['mockData.js', mockDataSrc],
    ...PUBLIC_COPY_FILES,
  ]
  for (const [name, src] of files) {
    it(`${name} claims no email-delivered alerts and no optional Telegram`, () => {
      if (!telegramRequiredForAlerts) return
      const offenders = deliveryOffenders(src)
      expect(offenders, `${name} inverted delivery-channel claim(s)`).toEqual([])
    })
  }

  it('Hero.jsx states the Telegram requirement where it names the channel', () => {
    if (!telegramRequiredForAlerts) return
    const mentions = sentences(heroSrc).filter(s => /telegram/i.test(s))
    if (mentions.length === 0) return
    const REQUIREMENT =
      /telegram[^.]{0,80}\b(required|requires?|need|must)\b|\b(required|requires?)\b[^.]{0,40}telegram/i
    // EVERY Telegram sentence that also talks about alert delivery must carry
    // the requirement — one honest sentence may not licence a softer one next
    // to it — and at least one such sentence must exist.
    const deliveryMentions = mentions.filter(s => /\balerts?\b|\bdeliver/i.test(s))
    const silent = deliveryMentions.filter(s => !REQUIREMENT.test(s))
    expect(
      silent,
      `Hero.jsx names Telegram alert delivery without stating it is required`,
    ).toEqual([])
    expect(
      deliveryMentions.length,
      `Hero.jsx names Telegram but never states the alert requirement: ${mentions.join(' | ').slice(0, 300)}`,
    ).toBeGreaterThan(0)
  })
})

// Guard-of-the-guard: the delivery-channel patterns must catch the FAMILY of
// rewrites (inflections, punctuation, channel-choice phrasing, homoglyphs),
// not the six literal shapes of the badge that was removed — and must NOT
// fire on the honest negative disclosure the iron rule asks authors to write.
describe('delivery-channel guard catches the rewrite family', () => {
  const MUST_TRIP = [
    'Email delivery included — Telegram optional.',
    'Telegram is entirely optional.',
    'Telegram remains optional.',
    'Telegram stays optional.',
    'Telegram: optional.',
    'Telegram integration is optional.',
    'Email or Telegram — your choice.',
    'Choose email or Telegram.',
    'Telegram or email, whichever you prefer.',
    'Prefer email? We support that too.',
    'Alerts also go to your email.',
    'Alerts are emailed to you the same day.',
    'Alerts reach you over email.',
    'Every alert lands in your inbox.',
    'Get alerts by email.',
    'Email alerts are included as standard.',
    'Connect Telegram if you want.',
    'Теlegram optional.', // Cyrillic homoglyph in "Telegram"
    'Telegram is a nice-to-have.',
    'Telegram is not required for alerts.',
    // An incidental negation elsewhere in the sentence must not launder an
    // affirmative delivery claim ("no credit card", "no setup", "without").
    'Alerts are delivered by email — no Telegram needed.',
    'No Telegram? Alerts still reach you by email.',
    'Alerts are delivered by email; no chat app required.',
    'No setup, no config — alerts are emailed to you.',
    'No credit card needed and alerts are delivered to your inbox daily.',
    'Get alerts by email without lifting a finger.',
    'Email delivery included, Telegram optional — no credit card needed.',
    'Alerts land in your email without any Telegram setup.',
    // Rewrite family: verb-first, opt-in, channel-list, mailbox, "+" pair.
    'We email you every alert.',
    'Telegram is opt-in.',
    'Telegram linking is not mandatory.',
    'Telegram is one of several delivery options.',
    'Every alert is pushed to your mailbox.',
    'No Telegram? Alerts still reach your inbox.',
    'Telegram? Only if you want it.',
    'Email works out of the box; link Telegram whenever you like.',
    'Weekly MLRO brief: Email + Telegram.',
    'Τelegram optional.', // Greek capital Tau in "Telegram"
    // Negation-INSIDE-the-span family (cycle-2 escalation): the negation sits
    // between the claim's subject and its verb, or after the verb as an aside,
    // and negates something OTHER than the delivery verb. The affirmative
    // claim survives, so the guard must still trip.
    'Alerts, no chat app required, are delivered to your inbox.',
    'Alerts are delivered — no Telegram — to your inbox.',
    'Alerts are delivered — no Telegram needed — to your inbox.',
    'Alerts, no chat app required, are delivered to your inbox daily.',
    'Alerts with no delay are delivered to your inbox.',
    'Alerts you never miss are emailed to you.',
    'Alerts, no matter the source, are delivered to your inbox.',
    'Alerts you cannot afford to miss are delivered to your inbox.',
    'Alerts are never delayed and land in your inbox within minutes.',
    'Alerts, no chat app required, are emailed to you.',
  ]
  for (const probe of MUST_TRIP) {
    it(`flags: ${probe}`, () => {
      expect(claimsInvertedDelivery(probe), probe).toBe(true)
    })
    // Same probe read the way a guarded FILE is read. sentences() used to
    // split on '?' before normalise() could fold it, so a unit probe could be
    // green while the file guard stayed silent on the same string.
    it(`flags in a guarded file: ${probe}`, () => {
      const fakeSrc = `export default function Fake() { return (<section><p>${probe}</p></section>) }`
      expect(deliveryOffenders(fakeSrc), probe).not.toEqual([])
    })
  }

  const MUST_PASS = [
    'Email delivery is not included; alerts require a linked Telegram chat.',
    'Alerts are not delivered by email.',
    'Alerts are delivered to Telegram — a linked chat is required.',
    'External email delivery is switched on by our team, never automatically.',
    'We send account email such as verification and password reset.',
    'No setup is required, and alerts are not delivered by email.',
    'Telegram is required for alerts; email carries account mail only.',
  ]
  for (const probe of MUST_PASS) {
    it(`allows: ${probe}`, () => {
      expect(claimsInvertedDelivery(probe), probe).toBe(false)
    })
  }
})

// The weekly MLRO brief has NO scheduled delivery on any channel today:
// app/weekly_brief.py only builds and writes the brief, and the sole delivery
// path (app/email_delivery.py) is reached from one user-triggered endpoint
// that writes a local test-mode outbox file. app/scheduler.py and run.py
// dispatch alert DIGESTS, not this brief. So /pricing may not sell the brief
// as arriving on a channel. Self-disarming: the moment a scheduler path names
// weekly_brief, the assertion stops applying.
describe('the weekly MLRO brief is priced as what it is', () => {
  // `run.py weekly-brief` exists but is a MANUAL operator command that writes
  // reports/weekly_briefs/*.md — it is not a sender and no timer runs it. Only
  // the watch-loop scheduler or a systemd unit counts as automated delivery.
  const scheduledSrcs = [
    '../app/scheduler.py',
    ...(existsSync(resolve(process.cwd(), '../deploy/systemd'))
      ? readdirSync(resolve(process.cwd(), '../deploy/systemd')).map(f => `../deploy/systemd/${f}`)
      : []),
  ]
    .map(r => resolve(process.cwd(), r))
    .filter(existsSync)
    .map(p => readFileSync(p, 'utf8'))
  const weeklyBriefIsScheduled = scheduledSrcs.some(s => /weekly[-_]brief/i.test(s))

  const pricingPageSrc = readFileSync(
    findFile(['src/components/PricingPage.jsx', 'web/src/components/PricingPage.jsx']),
    'utf8',
  )
  const briefValues = [
    ...copyOf(pricingPageSrc).matchAll(
      /label:\s*"Weekly MLRO brief"\s*,\s*value:\s*"([^"]*)"/g,
    ),
  ].map(m => m[1])

  it('PricingPage still lists the weekly MLRO brief', () => {
    expect(briefValues.length).toBeGreaterThan(0)
  })

  it('names no delivery channel for it while nothing delivers it', () => {
    if (weeklyBriefIsScheduled) return
    const offenders = briefValues.filter(v => /telegram/i.test(v))
    expect(offenders, 'weekly MLRO brief sold as a Telegram deliverable').toEqual([])
  })

  it('discloses that it is manual, not automated', () => {
    if (weeklyBriefIsScheduled) return
    const MANUAL = /\bmanual\b|\bon request\b|\broadmap\b|not automated/i
    const silent = briefValues.filter(v => !MANUAL.test(v))
    expect(silent, 'weekly MLRO brief value with no manual/roadmap disclosure').toEqual([])
  })
})

describe('public landing files carry no forbidden claims', () => {
  const FORBIDDEN = [
    /never miss/i,
    /guarantee[sd]? compliance/i,
    /prevent fines/i,
    /100% accurate/i,
    /stay compliant automatically/i,
    /certified by (the )?(DFSA|VARA|ADGM|CBUAE|SCA|CMA|DIFC)/i,
  ]
  const files = [
    ['index.html', indexHtml],
    ['Hero.jsx', heroSrc],
    ['App.jsx', appSrc],
    ['TrustLayer.jsx', trustLayerSrc],
    ['VerifyPage.jsx', verifyPageSrc],
    // New landing blocks (2026-07-21 build).
    ...PUBLIC_COPY_FILES.filter(([name]) =>
      ['EnforcementReality.jsx', 'Comparison.jsx', 'FaqSection.jsx', 'InlineVerify.jsx'].includes(name),
    ),
  ]
  for (const [name, src] of files) {
    for (const re of FORBIDDEN) {
      it(`${name} avoids ${re}`, () => {
        expect(re.test(copyOf(src)), `${name} contains forbidden claim ${re}`).toBe(false)
      })
    }
  }
})

// Enforcement-reality block (Block 4): the AED-fine / personal-liability cards
// are EXTERNAL regulatory news the reader can verify, never StatuteProof claims
// or predictions. So the block must (a) attribute every fact to an external
// source with a verifiable https link, (b) carry no fear-selling forbidden
// phrasing ("prevent fines", "avoid penalties"), and (c) never assert that
// StatuteProof monitors enforcement broadly in the present tense — enforcement
// monitoring beyond the disclosed fresh-alert sources is a stub (backlog #2).
describe('enforcement-reality block presents external news, not product claims', () => {
  const src = readFileSync(
    findFile(['src/components/EnforcementReality.jsx', 'web/src/components/EnforcementReality.jsx']),
    'utf8',
  )
  const copy = copyOf(src)

  it('attributes the cited facts to external sources with verifiable links', () => {
    expect(copy).toMatch(/https?:\/\//)
    expect(copy).toMatch(/report(ed|s|ing)|source:|as covered by|per /i)
  })

  it('never sells fine-avoidance (no forbidden fear claims)', () => {
    for (const re of [/prevent fines/i, /avoid (all )?(fines|penalties)/i, /never miss/i, /guarantee[sd]? compliance/i]) {
      expect(re.test(copy), `EnforcementReality contains ${re}`).toBe(false)
    }
  })

  it('makes no present-tense broad enforcement-monitoring scope claim', () => {
    const BROAD = [
      /\bwe monitor (all|every|each)\b[^.]{0,40}\benforcement\b/i,
      /monitor(s|ing)?\b[^.]{0,30}\b(all|every)\b[^.]{0,30}\benforcement (actions?|notices?)\b/i,
      /\benforcement\b[^.]{0,30}\bfully (monitored|covered)\b/i,
    ]
    const offenders = sentences(src).filter(s => BROAD.some(re => re.test(s)))
    expect(offenders, 'EnforcementReality broad enforcement-monitoring claim(s)').toEqual([])
  })
})

// Honest comparison block (Block 11): per the iron rule, our column may state
// only what WE do — never "no competitor does X" / "nobody else" / "only we".
describe('comparison block claims only what we do', () => {
  const src = readFileSync(
    findFile(['src/components/Comparison.jsx', 'web/src/components/Comparison.jsx']),
    'utf8',
  )
  const copy = copyOf(src)
  it('never asserts a universal competitor negative', () => {
    for (const re of [
      /no (other )?competitor\b/i,
      /nobody else\b/i,
      /no one else\b/i,
      /\bonly we\b/i,
      /\bthe only (vendor|tool|product|service)\b/i,
      /no (other )?(vendor|tool|product) (can|does|offers)/i,
    ]) {
      expect(re.test(copy), `Comparison contains universal-negative claim ${re}`).toBe(false)
    }
  })
})
