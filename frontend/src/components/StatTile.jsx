export default function StatTile({ label, value, accent = false }) {
  return (
    <div className="bg-panel border border-line rounded-lg px-4 py-3">
      <p className="text-xs text-ink-500 font-mono uppercase tracking-wide mb-1">
        {label}
      </p>
      <p
        className={`text-xl font-semibold font-mono ${
          accent ? "text-amber-400" : "text-ink-100"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
