# UI Review Prompt

Use this prompt to review the StatuteProof landing page or dashboard UI before any customer demo or public update.

---

## Prompt

```
You are reviewing the StatuteProof [landing page / dashboard] for customer readiness.

Apply #ui-ux-review skill.

Target audience: [CCO / MLRO / Head of Compliance] at a UAE-licensed financial firm.
Page: [URL or description]
Known issue to check: [describe the specific concern]

Step 1 — Mock Data Check
List every data point displayed on the page.
For each one, state: REAL (from live source_runs.jsonl) or MOCK (from mockData.js or appMockData.js).
Any MOCK data displayed without a SAMPLE / FAKE label is a HIGH-severity issue.

Step 2 — Trust Signal Check
For each displayed element (source health status, last-checked timestamp, hash, diff excerpt, risk score):
- Is it real or mock?
- Is it labeled correctly?
- Does it help or hurt credibility with a CCO?

Step 3 — Copy Safety
Check every headline, subheading, CTA, and badge against the forbidden phrase list.
One forbidden claim = BLOCK.

Step 4 — CTA Check
Is there one clear primary CTA?
Is the ask low-friction?
Does it match the product stage (pilot vs. full product)?

Step 5 — Source List Check
Does the displayed source list match the sources actually enabled in sources.json with real run records?

Output:
Mock data issues: [list or "none"]
Forbidden claims: [list or "none"]
Trust signal score: [1-10]
CTA quality: [1-10]
Copy safety: [PASS / BLOCK]
Source list accuracy: [ACCURATE / INFLATED]
Overall decision: DEMO-READY / REVISE / BLOCK
Required fixes before customer demo: [specific list]
```
