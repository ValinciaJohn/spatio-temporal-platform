// src/components/StatsBar.jsx
export default function StatsBar({ stats }) {
  const s = stats || {};

  const sil = s.silhouette ?? 0;
  const silColor = sil > 0.3 ? "green" : sil > 0 ? "yellow" : "red";
  const stab = s.stability ?? 1;
  const stabColor = stab >= 0.7 ? "green" : stab >= 0.55 ? "yellow" : "red";

  const lastUpd = s.last_updated
    ? new Date(s.last_updated * 1000).toLocaleTimeString()
    : "—";

  const cards = [
    { label: "CLUSTERS",    value: s.clusters     ?? 0, color: "cyan" },
    { label: "HOTSPOTS",    value: s.hotspots     ?? 0, color: s.hotspots > 0 ? "red" : "" },
    { label: "ANOMALIES",   value: s.anomalies    ?? 0, color: s.anomalies > 0 ? "yellow" : "" },
    { label: "BATCHES",     value: s.batches      ?? 0, color: "" },
    { label: "DRIFT EVENTS",value: s.drift_events ?? 0, color: s.drift_events > 0 ? "orange" : "" },
    { label: "SILHOUETTE",  value: sil.toFixed(3),      color: silColor },
    { label: "STABILITY",   value: stab.toFixed(3),     color: stabColor },
    { label: "NOISE %",     value: `${(s.noise_pct ?? 0).toFixed(1)}%`, color: "" },
    { label: "UPDATED",     value: lastUpd,             color: "", small: true },
  ];

  return (
    <div className="stats-bar">
      {cards.map((c) => (
        <div key={c.label} className={`stat-card ${c.color}`}>
          <div className="stat-label">{c.label}</div>
          <div className={`stat-value ${c.color} ${c.small ? "small-val" : ""}`}>
            {c.value}
          </div>
        </div>
      ))}
    </div>
  );
}