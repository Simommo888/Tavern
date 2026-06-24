import type { AnchorReply, LiveEvent, LiveRoomSession, ProductProfile } from '@/types/live';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://127.0.0.1:8770';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    cache: 'no-store',
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function createSession(product: ProductProfile): Promise<LiveRoomSession> {
  const payload = await request<{ session: LiveRoomSession }>('/api/v1/live/sessions', {
    method: 'POST',
    body: JSON.stringify(product),
  });
  return payload.session;
}

export async function sendAudienceEvent(sessionId: string, text: string): Promise<{ session: LiveRoomSession; reply: AnchorReply }> {
  return request(`/api/v1/live/sessions/${sessionId}/events`, {
    method: 'POST',
    body: JSON.stringify({ text, user_name: '模拟观众', source: 'workbench' }),
  });
}

export async function getSession(sessionId: string): Promise<{ session: LiveRoomSession; events: LiveEvent[] }> {
  return request(`/api/v1/live/sessions/${sessionId}`);
}

export async function latestSpeech(sessionId: string): Promise<AnchorReply | null> {
  const payload = await request<{ speech: AnchorReply | null }>(`/api/v1/live/sessions/${sessionId}/speech/latest`);
  return payload.speech;
}

export function absoluteApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export function eventStreamUrl(sessionId: string): string {
  return `${API_BASE}/api/v1/live/sessions/${sessionId}/events/stream`;
}
