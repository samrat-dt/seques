-- =============================================================================
-- Seques — Initial Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query → Run
-- =============================================================================

-- Sessions
create table if not exists sessions (
  id                      uuid primary key,
  provider                text not null,
  client_ip               text,
  questionnaire_type      text,
  questionnaire_filename  text,
  total_questions         int default 0,
  processing              boolean default false,
  created_at              timestamptz default now(),
  processing_started_at   timestamptz,
  processing_completed_at timestamptz
);

-- Questions (parsed from uploaded questionnaire)
create table if not exists questions (
  id            text not null,
  session_id    uuid not null references sessions(id) on delete cascade,
  text          text not null,
  answer_format text,
  category      text,
  original_row  int,
  primary key (id, session_id)
);

-- Answers (AI-generated, editable)
create table if not exists answers (
  question_id        text not null,
  session_id         uuid not null references sessions(id) on delete cascade,
  question_text      text,
  draft_answer       text,
  evidence_coverage  text,
  coverage_reason    text,
  ai_certainty       int,
  certainty_reason   text,
  answer_tone        text,
  needs_review       boolean,
  status             text default 'draft',
  evidence_sources   jsonb default '[]',
  suggested_addition text,
  updated_at         timestamptz default now(),
  primary key (question_id, session_id)
);

-- Audit events (immutable — do not update, only insert)
create table if not exists audit_events (
  event_id      uuid primary key,
  ts            timestamptz not null,
  unix_ms       bigint,
  action        text not null,
  actor         text,
  resource_type text,
  resource_id   text,
  outcome       text,
  request_id    text,
  detail        jsonb,
  created_at    timestamptz default now()
);

-- =============================================================================
-- Row Level Security
-- Enable RLS on all tables. In Phase 2 (with user auth), add per-user policies.
-- For now the service role key bypasses RLS entirely.
-- =============================================================================
alter table sessions     enable row level security;
alter table questions    enable row level security;
alter table answers      enable row level security;
alter table audit_events enable row level security;

-- =============================================================================
-- Indexes for common queries
-- =============================================================================
create index if not exists idx_questions_session  on questions(session_id);
create index if not exists idx_answers_session    on answers(session_id);
create index if not exists idx_audit_action       on audit_events(action);
create index if not exists idx_audit_resource     on audit_events(resource_id);
create index if not exists idx_audit_ts           on audit_events(ts desc);
