export default function DefinitionList({ items }: { items: Array<[string, string | number]> }) {
  return (
    <dl>
      {items.map(([label, value]) => (
        <div key={label} className="definition-row">
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
