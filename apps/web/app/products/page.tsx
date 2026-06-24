import WorkbenchShell from '@/components/live/WorkbenchShell';
import ProductCenter from '@/components/live/ProductCenter';
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
        <ProductCenter initialProducts={products} />
      </div>
    </WorkbenchShell>
  );
}
