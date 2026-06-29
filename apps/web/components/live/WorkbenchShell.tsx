import Link from 'next/link';

const navGroups = [
  {
    title: 'AI Company',
    items: [
      ['Home', '/dashboard'],
      ['Projects', '/projects'],
      ['Agents', '/agents'],
      ['Workflow', '/workflow'],
      ['Complete Video', '/complete-video'],
      ['Phase 9 MVP', '/mvp'],
      ['Studio', '/studio'],
    ],
  },
  {
    title: 'Production Assets',
    items: [
      ['Live Room', '/live-room'],
      ['Components', '/components'],
      ['Assets', '/assets'],
      ['Prompt Library', '/prompts'],
      ['Knowledge Base', '/knowledge'],
    ],
  },
  {
    title: 'Operations',
    items: [
      ['Analytics', '/analytics'],
      ['Model Manager', '/model-gateway'],
      ['Platform API', '/platform'],
      ['OBS Output', '/obs/demo'],
      ['Legacy Live Control', '/live-rooms/demo'],
    ],
  },
];

export default function WorkbenchShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand-mark">
          <span>TV</span>
          <div>
            <h1>Tavern LiveOS</h1>
            <p>AI Digital Live Commerce Operating System</p>
          </div>
        </div>
        <nav>
          {navGroups.map((group) => (
            <section key={group.title} className="nav-group">
              <strong>{group.title}</strong>
              {group.items.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}
            </section>
          ))}
        </nav>
      </aside>
      <section className="content">
        <header className="topbar">
          <div>
            <span className="eyebrow">AI Company Operating Layer</span>
            <strong>管理一家 AI 公司，而不是操作一个后台</strong>
          </div>
          <div className="topbar-actions">
            <input aria-label="search" placeholder="搜索 Project / Agent / Component / Prompt" />
            <button>新建直播项目</button>
          </div>
        </header>
        {children}
      </section>
    </main>
  );
}
