# Workflow 01: Weekly Planning

**When:** Every Monday or start of the working week.
**Agent:** Chief of Staff + `#weekly-founder-plan` skill.
**Output:** One weekly action plan with exactly 5 actions.

---

## Step 1 — Status Check

Before planning, gather actual status:

1. How many real run records exist? (`wc -l regradar/data/source_runs/source_runs.jsonl`)
2. Are there any CHANGED events from the past 7 days?
3. Is there any brief pending review?
4. Is there any outreach pending send?
5. Is there any dashboard or landing page update pending?

---

## Step 2 — Invoke Weekly Plan Skill

```
#weekly-founder-plan
Week: [YYYY-MM-DD]
Pipeline status: [number of enabled sources, last run date, any CHANGED events]
Pending items: [briefs, outreach, code tasks, content]
This week's focus: [source monitoring / evidence / brief / outreach / product]
```

---

## Step 3 — Review Plan Against Priorities

The weekly plan must respect this priority order:
1. Evidence dry run if any new source was added
2. Brief completion if any CHANGED event is unprocessed
3. Outreach only if a brief or evidence record exists to reference
4. Dashboard/landing update only after evidence exists
5. n8n / automation only after manual proof of concept

---

## Step 4 — Record and Execute

Write the 5-action plan in a dated note. Mark each action as done when complete.
Do not add more than 5 actions per week.
