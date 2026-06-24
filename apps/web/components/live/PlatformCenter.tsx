'use client';

import { useState } from 'react';
import { createPlatformEvent, createPlatformMetric } from '@/lib/api/workbench';
import type { PlatformEvent, PlatformMetricSnapshot } from '@/types/workbench';

export default function PlatformCenter({ initialEvents, initialMetrics }: { initialEvents: PlatformEvent[]; initialMetrics: PlatformMetricSnapshot[] }) {
  const [events, setEvents] = useState(initialEvents);
  const [metrics, setMetrics] = useState(initialMetrics);
  const [eventForm, setEventForm] = useState({ event_type: 'comment', user_name: '模拟观众', text: '这个酒真假怎么保证？', order_amount: '0' });
  const [metricForm, setMetricForm] = useState({ online_users: '1500', gmv: '88888', order_count: '420', interaction_rate: '0.21', conversion_rate: '0.05' });

  async function handleEvent() {
    const event = await createPlatformEvent({ ...eventForm, platform: 'manual', order_amount: Number(eventForm.order_amount) });
    setEvents((items) => [event, ...items]);
  }

  async function handleMetric() {
    const metric = await createPlatformMetric({
      platform: 'manual',
      online_users: Number(metricForm.online_users),
      gmv: Number(metricForm.gmv),
      order_count: Number(metricForm.order_count),
      interaction_rate: Number(metricForm.interaction_rate),
      conversion_rate: Number(metricForm.conversion_rate),
    });
    setMetrics((items) => [...items, metric]);
  }

  return (
    <section className="grid">
      <article className="card">
        <h2>模拟平台事件</h2>
        <label>事件类型<input value={eventForm.event_type} onChange={(event) => setEventForm({ ...eventForm, event_type: event.target.value })} /></label>
        <label>用户<input value={eventForm.user_name} onChange={(event) => setEventForm({ ...eventForm, user_name: event.target.value })} /></label>
        <label>内容<textarea value={eventForm.text} onChange={(event) => setEventForm({ ...eventForm, text: event.target.value })} /></label>
        <label>订单金额<input value={eventForm.order_amount} onChange={(event) => setEventForm({ ...eventForm, order_amount: event.target.value })} /></label>
        <button onClick={handleEvent}>写入事件</button>
      </article>
      <article className="card">
        <h2>写入指标快照</h2>
        <label>在线人数<input value={metricForm.online_users} onChange={(event) => setMetricForm({ ...metricForm, online_users: event.target.value })} /></label>
        <label>GMV<input value={metricForm.gmv} onChange={(event) => setMetricForm({ ...metricForm, gmv: event.target.value })} /></label>
        <label>成交单量<input value={metricForm.order_count} onChange={(event) => setMetricForm({ ...metricForm, order_count: event.target.value })} /></label>
        <label>互动率<input value={metricForm.interaction_rate} onChange={(event) => setMetricForm({ ...metricForm, interaction_rate: event.target.value })} /></label>
        <label>转化率<input value={metricForm.conversion_rate} onChange={(event) => setMetricForm({ ...metricForm, conversion_rate: event.target.value })} /></label>
        <button onClick={handleMetric}>写入指标</button>
      </article>
      <article className="card wide">
        <h2>平台事件流</h2>
        <pre>{JSON.stringify(events, null, 2)}</pre>
      </article>
      <article className="card wide">
        <h2>平台指标</h2>
        <pre>{JSON.stringify(metrics, null, 2)}</pre>
      </article>
    </section>
  );
}
