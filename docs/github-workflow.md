# GitHub Workflow

## Purpose

This workflow defines how a solo founder commits, validates, pushes, and tags Agent OS changes without leaking secrets or mixing unrelated work.
Even when the local folder is not initialized as a Git repository, these rules describe the expected repository discipline once version control is used.

## When To Commit

Commit after a coherent documentation, workflow, validator, checklist, or code change is complete and validated.
Do not commit half-written files.
Do not commit generated junk, backups, reference extracts, or local environment files.
Do not commit a broad cleanup mixed with a feature change unless the cleanup is necessary for the feature.

## Commit Message

Use `type(scope): description`.
Examples: `docs(v3.1): repair template operating docs`, `tools(validation): add clone detection`, `workflow(brief): enforce evidence-complete gate`.
The description should name the outcome, not the process.
Avoid vague messages like `updates` or `fix stuff`.

## Required Checks Before Commit

Run `python3 tools/validate_agent_os.py`.
Run `python3 tools/check_agent_uniqueness.py`.
Run `python3 tools/validate_json_files.py`.
Run `python3 tools/scan_for_forbidden_claims.py`.
Run `python3 tools/scan_for_secrets.py`.
Run `python3 tools/scan_for_placeholder_content.py`.
All must pass before commit.
If a script fails, fix the specific issue and rerun the full set.

## Branch Strategy for Solo Founder

Use `main` for stable versions only.
Use short-lived branches for repair passes, examples, validators, or docs upgrades.
Suggested branch names: `repair/v3-1-template-layer`, `docs/source-spec-pass`, `tools/validator-hardening`.
Keep one active branch per focused change.
Delete merged branches after confirming the tag or release note exists.

## Before Pushing

Check staged files match the intended scope.
Check no `.env` file is staged.
Check no API key, token, password, cookie, SSH key, or credential is staged.
Check no `reference_extracts` or private research dump is staged.
Check CHANGELOG.md has a clear entry for user-visible changes.
Check validation outputs are current.

## Commit Scope Rules

Never commit `.env` files.
Never commit credentials.
Never commit private keys.
Never commit raw reference extracts unless explicitly approved and scrubbed.
Never commit backup directories.
Never commit an 11th active agent without a versioned approval plan.
Never commit a new framework or dependency unless the founder explicitly approved it.
Never commit unrelated edits to protected agent files during a template repair pass.

## Rollback Procedure

Identify the bad commit or file set.
Prefer a revert commit over history rewriting once changes are shared.
Restore from the timestamped backup when the issue is local and not committed.
Run the validation scripts after rollback.
Record the rollback reason in CHANGELOG.md if it affects a released version.
Record any founder decision in memory/decisions.md.

## Version Tags

Use annotated tags for major documented versions.
Example: `git tag -a V3 -m "Agent OS V3"`.
Example: `git tag -a V3.1 -m "Template repair and operational upgrade"`.
Push tags only after validation passes and CHANGELOG.md is updated.
Do not tag a version with failing validation.

## CHANGELOG Rules

Add new entries at the top.
Keep prior version entries unchanged.
Use specific bullets that name changed files or file groups.
Mention validators when validation behavior changes.
Mention protected layers that were intentionally left untouched when relevant.
Do not use the changelog as a task list for unfinished work.
