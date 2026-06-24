import Link from 'next/link';

const navItems = [
  ['首页', '/dashboard'],
  ['直播间', '/live-rooms/demo'],
  ['商品中心', '/products'],
  ['数字人管理', '/avatars'],
  ['话术中心', '/scripts'],
  ['知识库 RAG', '/knowledge'],
  ['模型网关', '/model-gateway'],
  ['平台接入', '/platform'],
  ['工作流引擎', '/workflow'],
  ['数据中心', '/analytics'],
];

export default function WorkbenchShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="shell">
      <aside className="sidebar">
        <h1>Tavern Workbench</h1>
        <p>酒类 AI 数字人直播中台，面向品牌方、运营团队和 MCN。</p>
        <nav>
          {navItems.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}
        </nav>
      </aside>
      <section className="content">{children}</section>
    </main>
  );
}
