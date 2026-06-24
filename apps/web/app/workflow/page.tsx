import WorkbenchShell from '@/components/live/WorkbenchShell';
import { listWorkflowRules } from '@/lib/api/workbench';

const eventLabels: Record<string, string> = {
  user_enter: '用户进入',
  user_follow: '用户关注',
  fan_club_join: '用户加粉丝团',
  comment: '用户发弹幕',
  order_created: '用户下单',
  refund: '用户退款',
  cold_start: '直播冷场',
};

const actionLabels: Record<string, string> = {
  welcome: '欢迎用户',
  reply_comment: '回复弹幕',
  tell_story: '讲故事',
  sales_push: '促单转化',
  thank_order: '感谢下单',
  switch_product: '切换商品',
  run_script: '执行话术',
};

export default async function WorkflowPage() {
  const rules = await listWorkflowRules();
  return (
    <WorkbenchShell>
      <div className="page">
        <header className="hero">
          <div>
            <p className="eyebrow">Event Driven Workflow</p>
            <h1>工作流引擎</h1>
            <p>配置用户进入、关注、加粉丝团、发弹幕、下单、退款、冷场等事件触发流程。</p>
          </div>
          <button>新增规则</button>
        </header>
        <section className="grid">
          {rules.map((rule) => (
            <article key={rule.rule_id} className="card">
              <h2>{rule.name}</h2>
              <dl>
                <dt>事件</dt><dd>{eventLabels[rule.event_type] ?? rule.event_type}</dd>
                <dt>动作</dt><dd>{actionLabels[rule.action_type] ?? rule.action_type}</dd>
                <dt>延迟</dt><dd>{rule.delay_seconds} 秒</dd>
                <dt>状态</dt><dd>{rule.enabled ? '启用' : '停用'}</dd>
              </dl>
            </article>
          ))}
        </section>
      </div>
    </WorkbenchShell>
  );
}
