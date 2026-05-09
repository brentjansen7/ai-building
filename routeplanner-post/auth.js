import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.39.0/+esm';
import { ENV } from './config.js';

let supabaseUrl = ENV.SUPABASE_URL || localStorage.getItem('ENV_SUPABASE_URL') || '';
let supabaseAnonKey = ENV.SUPABASE_ANON_KEY || localStorage.getItem('ENV_SUPABASE_ANON_KEY') || '';

const hasRealCredentials = !!(supabaseUrl && supabaseAnonKey);

if (!hasRealCredentials) {
  if (!window.location.pathname.includes('setup.html')) {
    console.warn('⚠️ Missing Supabase credentials. Redirecting to setup...');
    window.location.href = 'setup.html';
  }
  supabaseUrl = supabaseUrl || 'https://placeholder.supabase.co';
  supabaseAnonKey = supabaseAnonKey || 'placeholder-key';
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
export { hasRealCredentials };

export async function getCurrentUser() {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

export async function getCurrentProfile() {
  const user = await getCurrentUser();
  if (!user) return null;

  const { data } = await supabase
    .from('profiles')
    .select('*, companies(name, kvk, plan_status)')
    .eq('id', user.id)
    .single();

  return data;
}

export async function signUp(email, password, companyName, kvk, billingAddress) {
  const { data: { user }, error: signupError } = await supabase.auth.signUp({
    email,
    password,
  });

  if (signupError) throw signupError;
  if (!user) throw new Error('Signup failed');

  const { data: company, error: companyError } = await supabase
    .from('companies')
    .insert([{
      name: companyName,
      kvk,
      billing_address: billingAddress,
      owner_user_id: user.id,
    }])
    .select()
    .single();

  if (companyError) throw companyError;

  const { error: profileError } = await supabase
    .from('profiles')
    .insert([{
      id: user.id,
      email,
      full_name: companyName,
      role: 'owner',
      company_id: company.id,
    }]);

  if (profileError) throw profileError;

  return { user, company };
}

export async function signIn(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) throw error;
  return data.user;
}

function getOAuthRedirectUrl() {
  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  if (isDev) {
    return window.location.origin + window.location.pathname.replace(/[^/]*$/, '') + 'auth-callback.html';
  }
  return 'https://brentjansen7.github.io/ai-building/routeplanner-post/auth-callback.html';
}

export async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: getOAuthRedirectUrl() },
  });
  if (error) throw error;
  return data;
}

export async function signInWithApple() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'apple',
    options: { redirectTo: getOAuthRedirectUrl() },
  });
  if (error) throw error;
  return data;
}

export async function ensureProfileExists(user) {
  const { data, error } = await supabase
    .from('profiles')
    .select('id')
    .eq('id', user.id)
    .maybeSingle();

  if (error) throw error;
  return !!data;
}

export async function completeOAuthProfile(user, companyName, kvk, billingAddress) {
  const { data: company, error: companyError } = await supabase
    .from('companies')
    .insert([{
      name: companyName,
      kvk,
      billing_address: billingAddress,
      owner_user_id: user.id,
    }])
    .select()
    .single();

  if (companyError) throw companyError;

  const { error: profileError } = await supabase
    .from('profiles')
    .insert([{
      id: user.id,
      email: user.email,
      full_name: user.user_metadata?.full_name || companyName,
      role: 'owner',
      company_id: company.id,
    }]);

  if (profileError) throw profileError;
  return { user, company };
}

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}

export async function getCompanyDrivers(companyId) {
  const { data } = await supabase
    .from('profiles')
    .select('*')
    .eq('company_id', companyId)
    .eq('role', 'driver');

  return data || [];
}

function generateSecureToken() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
}

export async function createInvite(companyId, email) {
  const token = generateSecureToken();
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();

  const { data, error } = await supabase
    .from('invites')
    .insert([{
      company_id: companyId,
      email,
      token,
      expires_at: expiresAt,
    }])
    .select()
    .single();

  if (error) throw error;
  return data;
}

export async function acceptInvite(token, password, fullName) {
  const { data: lookup, error: lookupError } = await supabase
    .rpc('lookup_invite', { invite_token: token });

  if (lookupError) throw lookupError;
  const invite = Array.isArray(lookup) ? lookup[0] : lookup;
  if (!invite || !invite.valid) throw new Error('Invite expired');

  const { data: { user }, error: signupError } = await supabase.auth.signUp({
    email: invite.email,
    password,
  });

  if (signupError) throw signupError;
  if (!user) throw new Error('Signup failed');

  const { error: profileError } = await supabase
    .from('profiles')
    .insert([{
      id: user.id,
      email: invite.email,
      full_name: fullName,
      role: 'driver',
      company_id: invite.company_id,
    }]);

  if (profileError) throw profileError;

  const { error: markError } = await supabase
    .rpc('mark_invite_used', { invite_token: token });

  if (markError) throw markError;

  return user;
}

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[c]));
}

export function onAuthStateChange(callback) {
  return supabase.auth.onAuthStateChange(callback);
}
