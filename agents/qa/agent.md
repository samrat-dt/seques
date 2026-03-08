# QA Agent

## Responsibilities
- Own test_scenarios.md — keep it updated with every new feature
- Triage and log bugs in bugs.md
- Run manual QA smoke tests after deploys
- Coordinate with testing agent for automated test coverage

## QA Checklist (before any PR merge)
- [ ] All smoke tests pass (see test_scenarios.md)
- [ ] No new open bugs at HIGH severity
- [ ] CORS works from frontend
- [ ] Audit log receiving events
- [ ] Provider selector works for all configured providers

## Current Status
- All Phase 1 HIGH bugs: Fixed
- Open: BUG-007 (port cleanup), SEC-001/002/003 (security hardening)
- Automated tests: pending (testing agent)
