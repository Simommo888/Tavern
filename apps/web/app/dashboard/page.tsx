import WorkbenchShell from '@/components/live/WorkbenchShell';
import { getDashboardSummary } from '@/lib/api/workbench';

const modules = [
  ['商品中心', '管理 SKU、售价、香型、度数、容量、卖点、适用场景和 FAQ。'],
  ['直播间管理', '创建直播间、绑定数字人、绑定商品池、控制直播状态。'],
  ['数字人管理', '维护真人素材、HeyGen Avatar、声音配置和生成任务。'],
  ['话术中心', '维护开场、讲品、促单、互动、感谢话术，并支持 AI 生成。'],
  ['数据中心', '观察 GMV、成交单量、在线人数、互动率和转化率。'],
  ['合规审计', '沉淀酒类合规规则、风险命中记录和模型输出审计。'],
];

export default async function DashboardPage() {
  const summary = await getDashboardSummary();
  const metrics = [
    ['在线人数', summary.online_users.toLocaleString('zh-CN')],
    ['当前 GMV', `¥${summary.current_gmv.toLocaleString('zh-CN')}`],
    ['今日成交额', `¥${summary.today_revenue.toLocaleString('zh-CN')}`],
    ['当前商品', summary.current_product?.product_name ?? '未配置'],
    ['数字人状态', summary.avatar_status],
    ['直播状态', summary.live_status],
  ];
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">AI Live Commerce Workbench</p>
            <h1>AI 数字人直播工作台</h1>
            <p>第一阶段聚焦酒类无人直播：自动讲品、回复弹幕、讲故事、促单、感谢下单和控制直播节奏。</p>
          </div>
          <a href="/live-rooms/demo"><button>进入直播总控</button></a>
        </header>

        <section className="metrics">
          {metrics.map(([label, value]) => (
            <article key={label} className="card metric">
              <span>{label}</span>
              <strong>{value}</strong>
            </article>
          ))}
        </section>

        <section className="grid">
          {modules.map(([title, description]) => (
            <article key={title} className="card">
              <h2>{title}</h2>
              <p>{description}</p>
            </article>
          ))}
        </section>
      </div>
    </WorkbenchShell>
  );
}
