// src/components/EvolutionLog.jsx
export default function EvolutionLog({ evolution }) {
  const items = (evolution || []).slice(-30).reverse();

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Cluster Evolution Log</span>
        <span className="panel-badge">LIFECYCLE TRACKING</span>
      </div>
      {items.length === 0 ? (
        <div className="no-data">No evolution events yet</div>
      ) : (
        <div className="evo-list">
          {items.map((ev, i) => {
            const state     = ev.state || "STABLE";
            const formatted = ev.formatted || `Cluster ${ev.cluster_id} ${state}`;
            const time      = ev.timestamp
              ? new Date(ev.timestamp * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
              : "";
            return (
              <div key={i} className={`evo-item ${state}`}>
                <span className={`evo-state ${state}`}>{state}</span>
                <span className="evo-text">{formatted}</span>
                <span className="evo-time">{time}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}