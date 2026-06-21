# StatuteProof visible redesign reference intake

Date: 2026-06-21

## References successfully inspected

- Local `design-taste-frontend` skill:
  `/Users/kurbnovomar/StatuteProof-Command-Center/.agents/skills/taste-skill/SKILL.md`
- Local `ui-ux-pro-max` skill:
  `/Users/kurbnovomar/StatuteProof-Command-Center/.agents/skills/ui-ux-pro-max/SKILL.md`
- Local `redesign-existing-projects` skill:
  `/Users/kurbnovomar/StatuteProof-Command-Center/.agents/skills/redesign-skill/SKILL.md`
- GitHub `leonxlnx/taste-skill`:
  `https://github.com/leonxlnx/taste-skill`
- GitHub `nextlevelbuilder/ui-ux-pro-max-skill`:
  `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill`
- YouTube motion-site reference:
  `https://youtu.be/uJU8MyCHGBI?si=ijqsFPisJIX-KCvo`
  - Metadata verified with `yt-dlp`: title `Вайбкодим БЕЗУМНЫЕ сайты с помощью Claude`, duration `893`, channel `Матвей Шульга`.
  - Russian subtitles were available and downloaded to `/tmp/statuteproof-video-reference/uJU8MyCHGBI.ru.vtt`.

## References not fully accessible

- The YouTube page did not expose rich page content through the browser/web open path.
- Full visual frame review of the video was not performed. The sprint may use the transcript and metadata, but must not claim frame-by-frame visual review.

## Video blocker

The video itself was not visually watched frame by frame in this environment. The usable evidence is the subtitle transcript plus metadata. Therefore, the redesign can honestly adopt transcript-level principles only:

- reference-first design work before coding
- one memorable product visual or interaction in the first viewport
- motion should create a clear cause/effect moment
- generated or animated visuals must be lightweight enough not to damage the site
- iteration is expected when the first effect is awkward

## Principles adopted from taste-skill

- Read the room before styling: this is a regulated B2B RegTech product, not an AI toy or consumer brand.
- Avoid generic centered dark SaaS with grid background, three equal cards, AI-purple/blue glow, and cosmetic animation.
- Set explicit dials:
  - Public site: design variance 5/10, motion intensity 3/10, visual density 4/10.
  - Dashboard: design variance 3/10, motion intensity 2/10, visual density 7/10.
- Use one coherent accent system. StatuteProof can keep cyan as an evidence/status accent, but the page needs stronger structure, depth, and information hierarchy than cyan-on-navy panels.
- Use CSS Grid and responsive constraints over fragile flex math.
- Make hero and CTA visible inside the first viewport.
- Use motion for hierarchy and state, not decoration.

## Principles adopted from ui-ux-pro-max

- Accessibility is a primary gate:
  - visible focus states
  - 44px+ touch targets
  - sufficient contrast
  - no icon-only critical controls without labels
- Mobile-first:
  - no horizontal body overflow
  - avoid dense tables as the primary mobile experience
  - put the highest-value task first on small screens
- Dashboard UX should support operator decisions:
  - what needs attention
  - source health flags
  - evidence records pending review
  - brief readiness and delivery gates
  - coverage limitations
- Animation must be 150-300ms, transform/opacity based, and compatible with `prefers-reduced-motion`.
- Forms need visible labels, inline errors, helper text for specialized terms, and clear disabled states.

## Principles adopted from redesign-existing-projects

- Audit before changing code.
- Work with the existing React/Vite/Tailwind stack.
- Do not rewrite from scratch.
- Replace same-looking generic panels with stronger composition, hierarchy, and task-specific components.
- Prioritize:
  1. visual system and layout structure
  2. typography and information hierarchy
  3. mobile card alternatives to wide tables
  4. hover/focus/active states
  5. empty/error/loading states

## What will not be copied

- No broad skill-pack install.
- No Ruflo, hooks, daemon, MCP memory, or background workers.
- No animation dependency unless explicitly approved.
- No decorative parallax, cursor gimmicks, auto-playing busy hero, or cinematic dashboard.
- No fake testimonials, fake users, fake evidence, fake source results, or fake customer proof.
- No complete UAE coverage, legal advice, guaranteed compliance, perfect parsing, never-miss, regulator certification, or all-source coverage claims.

## What is inappropriate for StatuteProof

- Wild motion-site effects as the product surface.
- A dashboard that looks like a landing page.
- Marketing cards that hide operational blockers.
- Tables that require horizontal scrolling as the only mobile path.
- Legal or compliance language that sounds like a lawyer, regulator, or certification body.
- Visual polish that makes an unproven delivery gate look production-ready.

## Final design read

Reading this as a regulated B2B RegTech product for UAE MLROs, CCOs, compliance managers, and founder-operators. Public site should feel premium, trustworthy, evidence-first, and materially more distinct than generic dark SaaS. Dashboard should feel like a calm operational command center, not a landing page.

The visible redesign should make the evidence workflow legible:

`Source run -> canonical evidence -> human review -> alert -> draft brief -> delivery approval`

The first visible product signal should be a product/evidence visual, not another generic dark hero card. Motion should clarify the chain and review states, while reduced-motion users receive the same information without animated movement.
