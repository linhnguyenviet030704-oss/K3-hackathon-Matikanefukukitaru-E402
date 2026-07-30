import { ChatSession, SymptomFilter } from './types';

const API_BASE_URL = ((import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://localhost:8000').replace(/\/$/, '');
const AUTH_TOKEN_KEY = 'supabase_access_token';
const AUTH_USER_KEY = 'dermacare_auth_user';
const SUPABASE_URL = (import.meta.env.VITE_SUPABASE_URL as string | undefined)?.replace(/\/$/, '');
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

export interface AuthUser {
  id: string;
  email: string;
}

const authHeaders = () => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const authConfigured = () => Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
const devToken = (email: string) => `dev-${encodeURIComponent(email.trim().toLowerCase())}`;

const saveAuth = (token: string, user: AuthUser) => {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  return user;
};

const authRequest = async (path: string, body: Record<string, unknown>) => {
  if (!authConfigured()) throw new Error('Supabase auth is not configured.');

  const response = await fetch(`${SUPABASE_URL}${path}`, {
    method: 'POST',
    headers: {
      apikey: SUPABASE_ANON_KEY!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.msg || error.message || 'Authentication failed.');
  }

  return response.json();
};

export const getStoredAuthUser = (): AuthUser | null => {
  try {
    const raw = localStorage.getItem(AUTH_USER_KEY);
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!raw || !token) return null;
    const user = JSON.parse(raw) as AuthUser;
    if (!authConfigured() && user.email && token !== devToken(user.email)) {
      return saveAuth(devToken(user.email), { id: user.email.trim().toLowerCase(), email: user.email.trim().toLowerCase() });
    }
    return user;
  } catch {
    return null;
  }
};

export const clearStoredAuth = () => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
};

export const signIn = async (email: string, password: string) => {
  if (!authConfigured()) {
    const normalizedEmail = email.trim().toLowerCase();
    return saveAuth(devToken(normalizedEmail), { id: normalizedEmail, email: normalizedEmail });
  }

  const data = await authRequest('/auth/v1/token?grant_type=password', { email, password });
  return saveAuth(data.access_token, { id: data.user.id, email: data.user.email });
};

export const signUp = async (email: string, password: string, name: string) => {
  if (!authConfigured()) {
    const normalizedEmail = email.trim().toLowerCase();
    return saveAuth(devToken(normalizedEmail), { id: normalizedEmail, email: normalizedEmail });
  }

  const data = await authRequest('/auth/v1/signup', {
    email,
    password,
    data: { name },
  });

  if (!data.access_token) {
    throw new Error('Đăng ký thành công. Vui lòng xác nhận email rồi đăng nhập.');
  }

  return saveAuth(data.access_token, { id: data.user.id, email: data.user.email });
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

export const listConversations = () => request<ChatSession[]>('/api/conversations');

export const createConversation = (title: string, isPublic = false) =>
  request<ChatSession>('/api/conversations', {
    method: 'POST',
    body: JSON.stringify({ title, isPublic }),
  });

export const updateConversation = (id: string, values: { title?: string; isPublic?: boolean }) =>
  request<ChatSession>(`/api/conversations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(values),
  });

export const deleteConversation = (id: string) =>
  request<{ ok: boolean }>(`/api/conversations/${id}`, { method: 'DELETE' });

export const clearConversations = () =>
  request<{ ok: boolean }>('/api/conversations', { method: 'DELETE' });

export const sendChatMessage = (payload: {
  conversationId?: string;
  message: string;
  imageBase64?: string | null;
  mimeType?: string;
  symptomSummary?: SymptomFilter;
  history?: Array<{ role: string; content: string }>;
}) =>
  request<{ text: string; citations: unknown[]; conversation: ChatSession }>('/api/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
