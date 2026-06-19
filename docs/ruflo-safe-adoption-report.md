# Ruflo Safe Adoption Report

Date: 2026-06-19

## Review Summary

Ruflo / claude-flow is potentially useful as an orchestration reference, but full installation is not recommended yet for StatuteProof.

Observed surface area from repository review:

- `.claude/` workspace files.
- `.agents/` skill and agent packs.
- hooks and pre-commit helpers.
- MCP server configuration.
- daemon/autopilot/memory concepts.
- many agent roles and commands.
- package scripts and optional dependencies.

## Useful Ruflo Ideas

- Explicit worker roles for adapter, validator, test fixture, source discovery, and security/tooling audit work.
- Task coordination with ownership and status.
- Memory of successful patterns, if later implemented with a project-controlled storage policy.
- Security/tooling audit role before adding external automation.
- Swarm-style parallel research for independent source families.

## Unsafe Or Not Yet Appropriate

- Full `npx ruflo init` in the StatuteProof workspace.
- Auto hooks on tool use, session start/end, or pre-commit.
- Daemon/autopilot background workers.
- MCP memory auto-sync without a data policy.
- Broad import of agent packs that can conflict with StatuteProof gates.
- Copying external `.claude/settings.json` permissions or model preferences.

## Recommended Safe Subset

- Do not install Ruflo full mode.
- Keep the Agent Council docs and local task board as the operating layer.
- Use existing Codex subagents for bounded read-only audits or assigned patches.
- Treat Ruflo agents as inspiration until a separate tooling-intake task proves installation is safe.

## Install Recommendation

No install now.

Exact install command: do not install yet.

## Future Re-Evaluation Trigger

Reconsider a limited Ruflo install only after:

- source/evidence validators are consolidated;
- customer claims are truth-cleaned;
- task board usage is stable;
- rollback plan is documented;
- founder explicitly approves the scope.
