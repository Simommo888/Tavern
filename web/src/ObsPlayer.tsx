import { useEffect, useMemo, useRef, useState } from 'react';
import { absoluteApiUrl, eventStreamUrl, getSession } from './api';
import type { AnchorReply, LiveEvent, LiveRoomSession } from './types';
import './style.css';

function parseAnchorReply(event: LiveEvent): AnchorReply | null {
  const reply = event.payload?.reply;
  if (!reply || typeof reply !== 'object') return null;
  return reply as AnchorReply;
}

export default function ObsPlayer() {
  const params = new URLSearchParams(window.location.search);
  const sessionId = params.get('session_id') || params.get('session') || '';
  const autoplay = params.get('autoplay') !== '0';
  const [session, setSession] = useState<LiveRoomSession | null>(null);
  const [latestReply, setLatestReply] = useState<AnchorReply | null>(null);
  const [status, setStatus] = useState(sessionId ? '连接中...' : '缺少 session_id');
  const [audioUnlocked, setAudioUnlocked] = useState(false);
  const playedIds = useRef(new Set<string>());

  useEffect(() => {
    if (!sessionId) return;
    getSession(sessionId)
      .then((snapshot) => {
        setSession(snapshot.session);
        setLatestReply(snapshot.session.recent_replies?.at(-1) ?? null);
        setStatus('等待主播回复');
      })
      .catch((error) => setStatus(`连接失败：${String(error)}`));
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;
    const source = new EventSource(eventStreamUrl(sessionId));
    source.addEventListener('anchor_reply', (message) => {
      try {
        const event = JSON.parse((message as MessageEvent).data) as LiveEvent;
        const reply = parseAnchorReply(event);
        if (reply) {
          setLatestReply(reply);
          setStatus('正在播报');
          if (autoplay) void playReply(reply);
        }
      } catch {
        setStatus('收到无法解析的事件');
      }
    });
    source.onerror = () => setStatus('事件流连接中断，浏览器会自动重连');
    return () => source.close();
  }, [sessionId, autoplay, audioUnlocked]);

  async function playReply(reply: AnchorReply) {
    if (!reply.speech_audio_url || playedIds.current.has(reply.reply_id)) return;
    playedIds.current.add(reply.reply_id);
    try {
      const audio = new Audio(absoluteApiUrl(reply.speech_audio_url));
      await audio.play();
      setAudioUnlocked(true);
      audio.onended = () => setStatus('等待主播回复');
    } catch {
      playedIds.current.delete(reply.reply_id);
      setStatus('浏览器阻止自动播放，请点击页面解锁音频');
    }
  }

  const title = useMemo(() => session?.product?.product_name || 'Tavern 数字人直播间', [session]);

  return (
    <main className="obs-stage" onClick={() => latestReply && playReply(latestReply)}>
      <section className="obs-room">
        <div className="obs-badge">LIVE</div>
        <div className="obs-avatar">酒</div>
        <div className="obs-info">
          <p className="eyebrow">Digital Human Anchor</p>
          <h1>{title}</h1>
          <p>{session?.product?.price || '直播间实时权益为准'}</p>
        </div>
      </section>
      <section className="obs-caption">
        <p>{latestReply?.text || '欢迎来到直播间，稍后主播将为大家介绍今日商品。'}</p>
        <small>{status}</small>
      </section>
    </main>
  );
}
