const statusText: Record<string, string> = {
  idle: '待命',
  working: '工作中',
  blocked: '阻塞',
  offline: '离线',
  running: '运行中',
  succeeded: '已完成',
  failed: '失败',
  queued: '排队中',
  active: '活跃',
  ready: '就绪',
  not_installed: '未安装',
};

export default function StatusBadge({ status }: { status: string }) {
  return <span className={`status status-${status}`}>{statusText[status] ?? status}</span>;
}
