'use client';

import { useState } from 'react';
import { createProduct, publishProduct, unpublishProduct } from '@/lib/api/workbench';
import type { ProductRecord } from '@/types/workbench';

export default function ProductCenter({ initialProducts }: { initialProducts: ProductRecord[] }) {
  const [products, setProducts] = useState(initialProducts);
  const [form, setForm] = useState({ product_name: '张裕解百纳礼盒', sku: 'ZHANGYU-CAB-750', price: '299', original_price: '399', aroma_type: '干红', alcohol_degree: '13%vol', volume: '750ml', selling_points: '品牌经典\n宴请送礼', scenes: '商务宴请\n送礼', faq_question: '适合商务宴请吗？', faq_answer: '适合成年人商务宴请和节日送礼场景。' });
  const [busy, setBusy] = useState(false);

  async function handleCreate() {
    setBusy(true);
    try {
      const product = await createProduct({
        product_name: form.product_name,
        sku: form.sku,
        price: Number(form.price),
        original_price: Number(form.original_price),
        aroma_type: form.aroma_type,
        alcohol_degree: form.alcohol_degree,
        volume: form.volume,
        selling_points: form.selling_points.split('\n').filter(Boolean),
        scenes: form.scenes.split('\n').filter(Boolean),
        faqs: [{ question: form.faq_question, answer: form.faq_answer }],
        status: 'draft',
      });
      setProducts((items) => [product, ...items]);
    } finally {
      setBusy(false);
    }
  }

  async function togglePublish(product: ProductRecord) {
    const next = product.status === 'published' ? await unpublishProduct(product.product_id) : await publishProduct(product.product_id);
    setProducts((items) => items.map((item) => item.product_id === next.product_id ? next : item));
  }

  return (
    <section className="grid">
      <article className="card wide">
        <h2>新增商品</h2>
        <div className="grid">
          <label>商品名称<input value={form.product_name} onChange={(event) => setForm({ ...form, product_name: event.target.value })} /></label>
          <label>SKU<input value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} /></label>
          <label>售价<input value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} /></label>
          <label>原价<input value={form.original_price} onChange={(event) => setForm({ ...form, original_price: event.target.value })} /></label>
          <label>香型<input value={form.aroma_type} onChange={(event) => setForm({ ...form, aroma_type: event.target.value })} /></label>
          <label>度数<input value={form.alcohol_degree} onChange={(event) => setForm({ ...form, alcohol_degree: event.target.value })} /></label>
          <label>容量<input value={form.volume} onChange={(event) => setForm({ ...form, volume: event.target.value })} /></label>
          <label>适用场景<textarea value={form.scenes} onChange={(event) => setForm({ ...form, scenes: event.target.value })} /></label>
          <label>卖点<textarea value={form.selling_points} onChange={(event) => setForm({ ...form, selling_points: event.target.value })} /></label>
          <label>FAQ 问题<input value={form.faq_question} onChange={(event) => setForm({ ...form, faq_question: event.target.value })} /></label>
          <label>FAQ 答案<textarea value={form.faq_answer} onChange={(event) => setForm({ ...form, faq_answer: event.target.value })} /></label>
        </div>
        <button onClick={handleCreate} disabled={busy}>{busy ? '保存中...' : '保存商品'}</button>
      </article>
      {products.map((product) => (
        <article key={product.product_id} className="card">
          <h2>{product.product_name}</h2>
          <dl>
            <dt>SKU</dt><dd>{product.sku}</dd>
            <dt>售价</dt><dd>¥{product.price}</dd>
            <dt>原价</dt><dd>¥{product.original_price}</dd>
            <dt>香型</dt><dd>{product.aroma_type || '-'}</dd>
            <dt>度数</dt><dd>{product.alcohol_degree || '-'}</dd>
            <dt>容量</dt><dd>{product.volume || '-'}</dd>
            <dt>状态</dt><dd>{product.status}</dd>
          </dl>
          <p><strong>卖点：</strong>{product.selling_points.join('、') || '未配置'}</p>
          <p><strong>场景：</strong>{product.scenes.join('、') || '未配置'}</p>
          <button onClick={() => togglePublish(product)}>{product.status === 'published' ? '下架商品' : '上架商品'}</button>
        </article>
      ))}
    </section>
  );
}
