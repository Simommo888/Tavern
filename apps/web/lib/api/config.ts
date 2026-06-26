const PUBLIC_API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://127.0.0.1:8770';

export function apiBase(): string {
  if (typeof window !== 'undefined') {
    return PUBLIC_API_BASE;
  }
  return process.env.TAVERN_API_BASE_INTERNAL ?? PUBLIC_API_BASE;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    cache: 'no-store',
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export function absoluteApiUrl(path: string): string {
  return `${apiBase()}${path}`;
}
