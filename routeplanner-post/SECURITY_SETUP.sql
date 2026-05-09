-- ============================================================================
-- Route Optimizer — Security Setup
-- Run this ONCE in Supabase Dashboard → SQL Editor → New Query
-- ============================================================================
-- Wat dit doet:
--  1) Helper functies (SECURITY DEFINER om RLS-recursie te vermijden)
--  2) RLS aanzetten op profiles, companies, invites
--  3) Policies: gebruikers zien alleen hun eigen data, admins zien alles
--  4) RPC voor invite-acceptatie (anonieme user met token)
-- ============================================================================

-- 1) Helper functies
CREATE OR REPLACE FUNCTION current_company_id()
RETURNS UUID LANGUAGE SQL SECURITY DEFINER STABLE AS $$
  SELECT company_id FROM profiles WHERE id = auth.uid()
$$;

CREATE OR REPLACE FUNCTION current_user_role()
RETURNS TEXT LANGUAGE SQL SECURITY DEFINER STABLE AS $$
  SELECT role FROM profiles WHERE id = auth.uid()
$$;

CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN LANGUAGE SQL SECURITY DEFINER STABLE AS $$
  SELECT (auth.jwt() ->> 'email') = 'brent.jansen2009@gmail.com'
$$;

-- 2) RLS aanzetten
ALTER TABLE profiles  ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE invites   ENABLE ROW LEVEL SECURITY;

-- 3) Bestaande policies droppen (idempotent)
DROP POLICY IF EXISTS profiles_select_own         ON profiles;
DROP POLICY IF EXISTS profiles_select_company     ON profiles;
DROP POLICY IF EXISTS profiles_insert_own         ON profiles;
DROP POLICY IF EXISTS profiles_update_own         ON profiles;
DROP POLICY IF EXISTS profiles_admin_all          ON profiles;

DROP POLICY IF EXISTS companies_select_member     ON companies;
DROP POLICY IF EXISTS companies_insert_owner      ON companies;
DROP POLICY IF EXISTS companies_update_owner      ON companies;
DROP POLICY IF EXISTS companies_admin_all         ON companies;

DROP POLICY IF EXISTS invites_select_owner        ON invites;
DROP POLICY IF EXISTS invites_insert_owner        ON invites;

-- 4) profiles policies
CREATE POLICY profiles_select_own ON profiles
  FOR SELECT USING (id = auth.uid());

CREATE POLICY profiles_select_company ON profiles
  FOR SELECT USING (company_id = current_company_id());

-- INSERT: alleen voor jezelf, en alleen rol 'owner' of 'driver'
CREATE POLICY profiles_insert_own ON profiles
  FOR INSERT WITH CHECK (
    id = auth.uid()
    AND role IN ('owner', 'driver')
  );

-- UPDATE: alleen je eigen profiel; rol en company_id mogen NIET veranderen
CREATE POLICY profiles_update_own ON profiles
  FOR UPDATE USING (id = auth.uid())
  WITH CHECK (
    id = auth.uid()
    AND role = current_user_role()
    AND company_id = current_company_id()
  );

CREATE POLICY profiles_admin_all ON profiles
  FOR ALL USING (is_admin()) WITH CHECK (is_admin());

-- 5) companies policies
CREATE POLICY companies_select_member ON companies
  FOR SELECT USING (id = current_company_id());

CREATE POLICY companies_insert_owner ON companies
  FOR INSERT WITH CHECK (owner_user_id = auth.uid());

CREATE POLICY companies_update_owner ON companies
  FOR UPDATE
  USING (owner_user_id = auth.uid() AND current_user_role() = 'owner')
  WITH CHECK (owner_user_id = auth.uid());

CREATE POLICY companies_admin_all ON companies
  FOR ALL USING (is_admin()) WITH CHECK (is_admin());

-- 6) invites policies (alleen owner van het bedrijf)
CREATE POLICY invites_select_owner ON invites
  FOR SELECT USING (
    company_id = current_company_id() AND current_user_role() = 'owner'
  );

CREATE POLICY invites_insert_owner ON invites
  FOR INSERT WITH CHECK (
    company_id = current_company_id() AND current_user_role() = 'owner'
  );

-- 7) RPC voor invite-acceptatie (anonieme user mag dit aanroepen met geldig token)
CREATE OR REPLACE FUNCTION lookup_invite(invite_token TEXT)
RETURNS TABLE(invite_id UUID, company_id UUID, email TEXT, valid BOOLEAN)
LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_invite RECORD;
BEGIN
  SELECT i.id, i.company_id, i.email INTO v_invite
  FROM invites i
  WHERE i.token = invite_token
    AND i.used_at IS NULL
    AND i.expires_at > NOW()
  LIMIT 1;

  IF NOT FOUND THEN
    RETURN QUERY SELECT NULL::UUID, NULL::UUID, NULL::TEXT, FALSE;
    RETURN;
  END IF;

  RETURN QUERY SELECT v_invite.id, v_invite.company_id, v_invite.email, TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION mark_invite_used(invite_token TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_count INTEGER;
BEGIN
  UPDATE invites
    SET used_at = NOW()
    WHERE token = invite_token
      AND used_at IS NULL
      AND expires_at > NOW();
  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count > 0;
END;
$$;

GRANT EXECUTE ON FUNCTION lookup_invite(TEXT)     TO anon, authenticated;
GRANT EXECUTE ON FUNCTION mark_invite_used(TEXT)  TO anon, authenticated;

-- ============================================================================
-- KLAAR. Test in Supabase Dashboard:
--   Authentication → Users (zie je eigen user)
--   Database → Tables → profiles → Policies (zie 5 policies)
--   Database → Tables → companies → Policies (zie 4 policies)
--   Database → Tables → invites → Policies (zie 2 policies)
-- ============================================================================
