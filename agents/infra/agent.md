# Infra Agent
> Supabase, CI/CD, deployment, environment management, monitoring.

## Responsibilities
- Supabase schema, migrations, RLS policies
- GitHub Actions CI/CD pipeline
- Environment variable management across dev/staging/prod
- Mixpanel dashboard setup
- Log shipping (audit.log → Supabase or external SIEM)

## Immediate Actions
1. **Run migration**: Paste `backend/migrations/001_initial_schema.sql` into Supabase SQL Editor at https://supabase.com/dashboard/project/deekxushpzcxmzdcvfxq/sql/new
2. **Verify tables exist**: sessions, questions, answers, audit_events
3. **Set up GitHub Actions** (see template below)

## GitHub Actions CI Template
Create `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.9' }
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest tests/ -v
```

## Mixpanel Dashboards to Create
1. Activation Funnel — session_created → export_downloaded
2. Provider A/B — processing_completed by provider, avg duration_ms
3. Quality — avg ai_certainty, needs_review rate
4. Errors — api_error by path + status_code

## Supabase RLS Note
Tables have RLS enabled. Service role key bypasses it.
Phase 2: add per-user policies when auth is implemented.
