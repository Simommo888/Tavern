import { useEffect, useMemo, useState } from 'react';
import { absoluteApiUrl, createSession, eventStreamUrl, getSession, latestSpeech, sendAudienceEvent } from './api';
import type { AnchorReply, LiveEvent, LiveRoomSession, ProductProfile } from './types';
import './style.css';

const defaultProduct: ProductProfile = {
  product_name: '酱香酒端午礼盒',
  brand: 'Tavern 示例品牌',
  price: '直播间实时权益为准',
  specification: '礼盒装',
  selling_points: ['端午送礼', '礼盒包装', '成熟消费者宴请场景'],
  promotions: ['限时组合权益'],
};

export default function App() {
  const [product, setProduct] = useState<ProductProfile>(defaultProduct);
  const [session, setSession] = useState<LiveRoomSession | null>(null);
  const [question, setQuestion] = useState('这个适合送领导吗？');
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [replies, setReplies] = useState<AnchorReply[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [speechEnabled, setSpeechEnabled] = useState(false);
  const [lastSpokenId, setLastSpokenId] = useState('');

  const canSend = useMemo(() => Boolean(session && question.trim() && !busy), [session, question, busy]);

  useEffect(() => {
    if (!session) return;
    const source = new EventSource(eventStreamUrl(session.session_id));
    const appendEvent = (message: MessageEvent) => {
      try {
        const event = JSON.parse(message.data) as LiveEvent;
        setEvents((items) => [...items, event].slice(-80));
      } catch {
        return;
      }
    };
    source.onmessage = appendEvent;
    ['session_created', 'audience_event', 'speech_artifact', 'anchor_reply', 'session_stopped'].forEach((type) => {
      source.addEventListener(type, appendEvent);
    });
    return () => source.close();
  }, [session?.session_id]);

  useEffect(() => {
    if (!speechEnabled || replies.length === 0) return;
    const reply = replies[replies.length - 1];
    if (!reply || reply.reply_id === lastSpokenId) return;
    playSpeech(reply);
    setLastSpokenId(reply.reply_id);
  }, [speechEnabled, replies, lastSpokenId]);

  function playSpeech(reply: AnchorReply) {
    if (reply.speech_audio_url) {
      const audio = new Audio(absoluteApiUrl(reply.speech_audio_url));
      audio.play().catch(() => speakWithBrowser(reply.text));
      return;
    }
    speakWithBrowser(reply.text);
  }

  function speakWithBrowser(text: string) {
    if (!('speechSynthesis' in window)) {
      setError('当前浏览器不支持 Web Speech API');
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = 1.03;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }

  async function handlePollLatestSpeech() {
    if (!session) return;
    const speech = await latestSpeech(session.session_id);
    if (speech) setReplies((items) => [...items.filter((item) => item.reply_id !== speech.reply_id), speech].slice(-20));
  }

  async function handleCreate() {
    setBusy(true);
    setError('');
    try {
      const next = await createSession(product);
      setSession(next);
      const snapshot = await getSession(next.session_id);
      setEvents(snapshot.events);
      setReplies(snapshot.session.recent_replies ?? []);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSend() {
    if (!session) return;
    setBusy(true);
    setError('');
    try {
      const payload = await sendAudienceEvent(session.session_id, question);
      setSession(payload.session);
      setReplies((items) => [...items, payload.reply].slice(-20));
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Tavern Live Room</p>
          <h1>实时互动数字人直播间控制台</h1>
          <p>前后端分离 MVP：创建直播间、模拟弹幕、查看主播大脑回复和合规状态。</p>
        </div>
        <button onClick={handleCreate} disabled={busy}>{session ? '重建直播间' : '创建直播间'}</button>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="grid">
        <div className="card">
          <h2>商品配置</h2>
          <label>商品名<input value={product.product_name} onChange={(e) => setProduct({ ...product, product_name: e.target.value })} /></label>
          <label>品牌<input value={product.brand ?? ''} onChange={(e) => setProduct({ ...product, brand: e.target.value })} /></label>
          <label>价格/权益<input value={product.price ?? ''} onChange={(e) => setProduct({ ...product, price: e.target.value })} /></label>
          <label>卖点<textarea value={(product.selling_points ?? []).join('\n')} onChange={(e) => setProduct({ ...product, selling_points: e.target.value.split('\n').filter(Boolean) })} /></label>
        </div>

        <div className="card">
          <h2>直播间状态</h2>
          <dl>
            <dt>Session</dt><dd>{session?.session_id ?? '未创建'}</dd>
            <dt>状态</dt><dd>{session?.status ?? '-'}</dd>
            <dt>用户事件</dt><dd>{session?.event_count ?? 0}</dd>
            <dt>主播回复</dt><dd>{session?.reply_count ?? 0}</dd>
          </dl>
          <div className="speech-controls">
            <button onClick={() => setSpeechEnabled((value) => !value)}>{speechEnabled ? '关闭自动播报' : '开启自动播报'}</button>
            <button onClick={() => replies.at(-1) && playSpeech(replies.at(-1)!)} disabled={replies.length === 0}>重播最新回复</button>
            <button onClick={handlePollLatestSpeech} disabled={!session}>拉取最新 speech</button>
          </div>
        </div>

        <div className="card wide">
          <h2>模拟观众互动</h2>
          <div className="ask-row">
            <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="输入观众弹幕/问题" />
            <button onClick={handleSend} disabled={!canSend}>发送给主播</button>
          </div>
          <div className="quick">
            {['多少钱？', '适合送领导吗？', '喝了是不是养生？', '今天有什么优惠？'].map((item) => <button key={item} onClick={() => setQuestion(item)}>{item}</button>)}
          </div>
        </div>

        <div className="card wide">
          <h2>主播回复 / 浏览器 TTS 播报</h2>
          <div className="timeline">
            {replies.map((reply) => (
              <article key={reply.reply_id} className="reply">
                <span>{reply.intent}</span>
                <p>{reply.text}</p>
                {reply.speech_artifact_id && <small>Speech artifact: {reply.speech_artifact_id}</small>}
                {!reply.compliance_passed && <small>合规改写：{reply.compliance_notes.join('、')}</small>}
              </article>
            ))}
          </div>
        </div>

        <div className="card wide">
          <h2>事件日志</h2>
          <pre>{events.slice(-20).map((event) => `${event.created_at} ${event.type}`).join('\n') || '暂无事件'}</pre>
        </div>
      </section>
    </main>
  );
}
