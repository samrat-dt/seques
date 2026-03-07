# GitHub Agent
> Owns all GitHub operations: PRs, issues, branches, CI, releases.

## Responsibilities
- Create and manage branches (feature/, fix/, chore/)
- Open PRs with context from agents/shared/decisions.md
- Triage and label issues
- Set up GitHub Actions CI (see infra agent)
- Manage releases and changelogs
- Enforce branch protection on main

## Branch Naming
```
feature/[agent]-[description]   e.g. feature/backend-supabase-auth
fix/[agent]-[description]       e.g. fix/security-cors-wildcard
chore/[agent]-[description]     e.g. chore/infra-ci-setup
```

## PR Template (always use)
```
## What
[One line summary]

## Why
[Link to decision in agents/shared/decisions.md or backlog item]

## Test plan
- [ ] Backend: .venv/bin/pytest tests/
- [ ] Manual: upload doc + questionnaire → answers generated
- [ ] QA checklist item: [which scenario]

## Compliance impact
[None / SOC2 / GDPR / ISO — which controls affected]
```

## Immediate Setup Needed
- [ ] Create `.github/dependabot.yml` (security agent dependency)
- [ ] Create `.github/workflows/ci.yml` (infra agent template)
- [ ] Enable branch protection on main: require PR + 1 review
- [ ] Add issue labels: bug, p0, p1, p2, backend, frontend, compliance, security

## Commands (use gh CLI)
```bash
gh pr create --title "..." --body "..."
gh issue create --title "..." --label "bug,p1"
gh issue list --label "p0"
gh pr list --state open
```

## Current Repo State
- Branch: main
- Last commit: feat: initial Phase 1 build
- CI: not set up yet
- Branch protection: not enabled yet
