export type MetricItem = {
  label: string;
  value: string | number;
  hint?: string;
};

export default function MetricGrid({ metrics }: { metrics: MetricItem[] }) {
  return (
    <section className="metrics">
      {metrics.map((metric) => (
        <article key={metric.label} className="card metric">
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          {metric.hint && <small>{metric.hint}</small>}
        </article>
      ))}
    </section>
  );
}
