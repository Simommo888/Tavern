import { absoluteApiUrl, apiRequest } from '@/lib/api/config';
import type { AnchorReply, LiveEvent, LiveRoomSession, ProductProfile } from '@/types/live';

export async function createSession(product: ProductProfile): Promise<LiveRoomSession> {
  const payload = await apiRequest<{ session: LiveRoomSession }>('/api/v1/live/sessions', {
    method: 'POST',
    body: JSON.stringify(product),
  });
  return payload.session;
}

export async function sendAudienceEvent(sessionId: string, text: string): Promise<{ session: LiveRoomSession; reply: AnchorReply }> {
  return apiRequest<{ session: LiveRoomSession; reply: AnchorReply }>(`/api/v1/live/sessions/${sessionId}/events`, {
    method: 'POST',
    body: JSON.stringify({ text, user_name: '模拟观众', source: 'workbench' }),
  });
}

export async function getSession(sessionId: string): Promise<{ session: LiveRoomSession; events: LiveEvent[] }> {
  return apiRequest<{ session: LiveRoomSession; events: LiveEvent[] }>(`/api/v1/live/sessions/${sessionId}`);
}

export async function latestSpeech(sessionId: string): Promise<AnchorReply | null> {
  const payload = await apiRequest<{ speech: AnchorReply | null }>(`/api/v1/live/sessions/${sessionId}/speech/latest`);
  return payload.speech;
}

export { absoluteApiUrl };

export function eventStreamUrl(sessionId: string): string {
  return absoluteApiUrl(`/api/v1/live/sessions/${sessionId}/events/stream`);
}
