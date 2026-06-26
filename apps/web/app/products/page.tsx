import WorkbenchShell from '@/components/live/WorkbenchShell';
import ProductCenter from '@/components/live/ProductCenter';
import PageHero from '@/components/ui/PageHero';
import { listProducts } from '@/lib/api/workbench';

export default async function ProductsPage() {
  const products = await listProducts();
  return (
    <WorkbenchShell>
      <div className="page">
        <PageHero
          eyebrow="Project / Product Intelligence"
          title="商品资料是 Agent 的输入资产"
          description="管理 SKU、价格、香型、度数、容量、卖点、场景和 FAQ，供 Product Analyst Agent 与 Script Agent 复用。"
          action={<button>新增商品</button>}
        />
        <ProductCenter initialProducts={products} />
      </div>
    </WorkbenchShell>
  );
}
