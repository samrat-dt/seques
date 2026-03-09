-- ============================================================================
-- Migration 002: Row-Level Security policies for multi-tenant auth
-- Run after: 001_initial_schema.sql
-- Requires: Supabase Auth enabled on the project
-- ============================================================================

-- Add user_id column to sessions (FK to auth.users)
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL;

-- Index for fast per-user session lookups
CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions(user_id);

-- ============================================================================
-- Enable RLS on all tables
-- ============================================================================

ALTER TABLE sessions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE answers       ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events  ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Sessions policies
-- ============================================================================

-- Users can only read their own sessions
CREATE POLICY "sessions_select_own"
  ON sessions FOR SELECT
  USING (user_id = auth.uid());

-- Users can only insert sessions owned by themselves
CREATE POLICY "sessions_insert_own"
  ON sessions FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- Users can only update their own sessions
CREATE POLICY "sessions_update_own"
  ON sessions FOR UPDATE
  USING (user_id = auth.uid());

-- ============================================================================
-- Questions policies (inherit session ownership)
-- ============================================================================

CREATE POLICY "questions_select_own"
  ON questions FOR SELECT
  USING (
    session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
  );

CREATE POLICY "questions_insert_own"
  ON questions FOR INSERT
  WITH CHECK (
    session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
  );

-- ============================================================================
-- Answers policies (inherit session ownership)
-- ============================================================================

CREATE POLICY "answers_select_own"
  ON answers FOR SELECT
  USING (
    session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
  );

CREATE POLICY "answers_insert_own"
  ON answers FOR INSERT
  WITH CHECK (
    session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
  );

CREATE POLICY "answers_update_own"
  ON answers FOR UPDATE
  USING (
    session_id IN (SELECT id FROM sessions WHERE user_id = auth.uid())
  );

-- ============================================================================
-- Audit events — INSERT-only for app role, SELECT for owner
-- ============================================================================

-- The backend service role can insert audit events for any session
CREATE POLICY "audit_events_insert_service"
  ON audit_events FOR INSERT
  WITH CHECK (true);  -- enforced at app layer; service key bypasses RLS

-- Users can read audit events for their own sessions
CREATE POLICY "audit_events_select_own"
  ON audit_events FOR SELECT
  USING (
    resource_id IN (SELECT id::text FROM sessions WHERE user_id = auth.uid())
  );

-- ============================================================================
-- Service role bypass (backend uses SUPABASE_SERVICE_KEY which bypasses RLS)
-- No additional grants needed — service role is superuser equivalent.
-- ============================================================================
