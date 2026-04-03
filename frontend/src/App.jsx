import { useState, useEffect, useCallback } from "react";
import StatsBar from "./components/StatsBar";
import MapPanel from "./components/MapPanel";
import ClusterTable from "./components/ClusterTable";
import AlertFeed from "./components/AlertFeed";
import RegimeChart from "./components/RegimeChart";
import DriftPanel from "./components/DriftPanel";
import EvolutionLog from "./components/EvolutionLog";

const API = "http://localhost:8000/api";
const REFRESH_MS = 5000;

function usePoll(endpoint, defaultVal) {
  const [data, setData] = useState(defaultVal);
  const [loading, setLoading] = useState(true);

  const fetch_ = useCallback(async () => {
    try {
      const r = await fetch(`${API}${endpoint}`);
      if (r.ok) setData(await r.json());
    } catch (_) {}
    setLoading(false);
  }, [endpoint]);

  useEffect(() => {
    fetch_();
    const id = setInterval(fetch_, REFRESH_MS);
    return () => clearInterval(id);
  }, [fetch_]);

  return { data, loading };
}

export default function App() {
  const { data: stats }     = usePoll("/stats",     {});
  const { data: summary }   = usePoll("/summary",   []);
  const { data: alerts }    = usePoll("/alerts",    []);
  const { data: evolution } = usePoll("/evolution", []);
  const { data: drift }     = usePoll("/drift",     {});
  const [tick, setTick]     = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  const isLive = stats.last_updated && (Date.now() / 1000 - stats.last_updated) < 15;

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-left">
          <div className="logo-mark">⬡</div>
          <div>
            <h1 className="title">TRAFFIC INTELLIGENCE</h1>
            <p className="subtitle">Spatio-Temporal Mining Platform · Coimbatore, TN</p>
          </div>
        </div>
        <div className="header-right">
          <div className={`live-badge ${isLive ? "live" : "offline"}`}>
            <span className="pulse-dot" />
            {isLive ? "LIVE" : "OFFLINE"}
          </div>
          <div className="team-tag">22PD04 · AKILA</div>
        </div>
      </header>

      {/* ── Stats Bar ── */}
      <StatsBar stats={stats} />

      {/* ── Main Grid ── */}
      <main className="main-grid">
        {/* Left column */}
        <div className="col-left">
          <MapPanel tick={tick} />
          <ClusterTable summary={summary} />
        </div>

        {/* Right column */}
        <div className="col-right">
          <AlertFeed alerts={alerts} />
          <RegimeChart summary={summary} />
          <DriftPanel drift={drift} />
          <EvolutionLog evolution={evolution} />
        </div>
      </main>

      <footer className="footer">
        Spatio-Temporal Mining Platform · ST-DBSCAN + Kafka + DTW · Ref: Shekhar et al. 2015
      </footer>
    </div>
  );
}