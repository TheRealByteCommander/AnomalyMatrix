export default function StatusBadge({ state, children }) {
  return <span className={`state state-${state}`}>{children}</span>;
}
