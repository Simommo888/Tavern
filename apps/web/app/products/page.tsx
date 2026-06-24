import WorkbenchShell from '@/components/live/WorkbenchShell';
import { listProducts } from '@/lib/api/workbench';

export default async function ProductsPage() {
  const products = await listProducts();
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Product Center</p>
            <h1>商品中心</h1>
            <p>管理酒类商品的 SKU、价格、香型、度数、容量、卖点、适用场景和 FAQ。</p>
          </div>
          <button>新增商品</button>
        </header>
        <section className="grid">
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
              <div className="timeline">
                {product.faqs.map((faq) => (
                  <article key={faq.question} className="reply">
                    <span>FAQ</span>
                    <p>{faq.question}</p>
                    <small>{faq.answer}</small>
                  </article>
                ))}
              </div>
            </article>
          ))}
        </section>
      </div>
    </WorkbenchShell>
  );
}
