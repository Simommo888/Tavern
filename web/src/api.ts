import type { AnchorReply, LiveEvent, LiveRoomSession, ProductProfile } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8765';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function createSession(product: ProductProfile): Promise<LiveRoomSession> {
  const payload = await request<{ session: LiveRoomSession }>('/api/live/sessions', {
    method: 'POST',
    body: JSON.stringify(product),
  });
  return payload.session;
}

export async function sendAudienceEvent(sessionId: string, text: string): Promise<{ session: LiveRoomSession; reply: AnchorReply }> {
  return request(`/api/live/sessions/${sessionId}/events`, {
    method: 'POST',
    body: JSON.stringify({ text, user_name: '模拟观众', source: 'web' }),
  });
}

export async function getSession(sessionId: string): Promise<{ session: LiveRoomSession; events: LiveEvent[] }> {
  return request(`/api/live/sessions/${sessionId}`);
}

export async function latestSpeech(sessionId: string): Promise<AnchorReply | null> {
  const payload = await request<{ speech: AnchorReply | null }>(`/api/live/sessions/${sessionId}/speech/latest`);
  return payload.speech;
}

export function absoluteApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export function eventStreamUrl(sessionId: string): string {
  return `${API_BASE}/api/live/sessions/${sessionId}/events/stream`;
}
