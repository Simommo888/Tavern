export default function ProgressBar({ value }: { value: number }) {
  const percent = Math.max(0, Math.min(100, Math.round(value * 100)));
  return <div className="progress"><span style={{ width: `${percent}%` }} /><em>{percent}%</em></div>;
}
