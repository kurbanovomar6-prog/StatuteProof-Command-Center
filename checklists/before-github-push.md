# Checklist: Before GitHub Push

Complete all items before pushing any StatuteProof-related code or docs to a GitHub repository.

## Secrets

- [ ] `.env` file is not staged (`git status` shows no .env)
- [ ] `.env.*` files are not staged
- [ ] No API keys, tokens, passwords, or credentials in any staged file
- [ ] `grep -r "sk-" .` returns no results in staged files (or results are in test fixtures and non-sensitive)
- [ ] OPENAI_API_KEY, ANTHROPIC_API_KEY, and any other key is not hardcoded

## Reference and Archive Files

- [ ] `.reference_tmp/` is not staged (excluded by .gitignore)
- [ ] `.reference_extracts/`, `.reference_review_extracts/` are not staged
- [ ] `dist/` is not staged
- [ ] `node_modules/` is not staged
- [ ] `*.zip` files are not staged
- [ ] `*_BACKUP_*` folders are not staged

## Placeholder and Sample Content

- [ ] No placeholder text ("lorem ipsum", "TODO", "TBD") in production-path files
- [ ] Any SAMPLE / FAKE example files are labeled at the top of the file
- [ ] No invented evidence record IDs or hashes in production source code

## Code Quality (regradar pushes)

- [ ] Tests pass: `cd regradar && python3 -m pytest tests/ -q`
- [ ] No print statements left in production code paths
- [ ] No hardcoded source URLs that differ from sources.json

## Commit Message

- [ ] Commit message describes what changed and why (not just "update files")
- [ ] Commit message does not include sensitive context (customer names, internal decisions)

## Final

- [ ] `git status` reviewed — only intended files staged
- [ ] `git diff --cached` reviewed — all changes understood
- [ ] Push target is the correct repository and branch
