import { useState, useEffect, useCallback, useRef } from "react";
import StatsBar from "./components/StatsBar";
import MapPanel from "./components/MapPanel";
import ClusterTable from "./components/ClusterTable";
import AlertFeed from "./components/AlertFeed";
import RegimeChart from "./components/RegimeChart";
import DriftPanel from "./components/DriftPanel";
import EvolutionLog from "./components/EvolutionLog";

const API = "/api";
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

// ─── Services Control Panel ───────────────────────────────────────────────────
const SERVICES = [
  {
    id: "kafka",
    label: "Kafka Producer",
    icon: "⬡",
    desc: "Streams traffic events to Kafka topic",
    cmd: "kafka",
    color: "var(--accent2)",
  },
  {
    id: "pipeline",
    label: "ST-DBSCAN Pipeline",
    icon: "◈",
    desc: "Spatio-temporal clustering + drift detection",
    cmd: "pipeline",
    color: "var(--accent)",
  },
];

function ServicesPanel() {
  const [statuses, setStatuses] = useState({ kafka: false, pipeline: false });
  const [logs, setLogs] = useState({ kafka: [], pipeline: [] });
  const [loading, setLoading] = useState({ kafka: false, pipeline: false });
  const logRefs = useRef({});

  // Poll service statuses
  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${API}/services/status`);
        if (r.ok) {
          const d = await r.json();
          setStatuses(d);
        }
      } catch (_) {}
    };
    check();
    const id = setInterval(check, 3000);
    return () => clearInterval(id);
  }, []);

  // Poll logs per service
  useEffect(() => {
    const poll = async () => {
      for (const svc of SERVICES) {
        try {
          const r = await fetch(`${API}/services/logs/${svc.id}?lines=40`);
          if (r.ok) {
            const d = await r.json();
            setLogs(prev => ({ ...prev, [svc.id]: d.lines || [] }));
          }
        } catch (_) {}
      }
    };
    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, []);

  // Auto-scroll logs
  useEffect(() => {
    for (const key of Object.keys(logRefs.current)) {
      const el = logRefs.current[key];
      if (el) el.scrollTop = el.scrollHeight;
    }
  }, [logs]);

  const toggle = async (svc) => {
    const running = statuses[svc.id];
    setLoading(prev => ({ ...prev, [svc.id]: true }));
    try {
      const action = running ? "stop" : "start";
      await fetch(`${API}/services/${action}/${svc.id}`, { method: "POST" });
      setTimeout(() => setLoading(prev => ({ ...prev, [svc.id]: false })), 1200);
    } catch (_) {
      setLoading(prev => ({ ...prev, [svc.id]: false }));
    }
  };

  const startAll = async () => {
    for (const svc of SERVICES) {
      if (!statuses[svc.id]) {
        await fetch(`${API}/services/start/${svc.id}`, { method: "POST" });
        await new Promise(r => setTimeout(r, 800));
      }
    }
  };

  const stopAll = async () => {
    for (const svc of SERVICES) {
      if (statuses[svc.id]) {
        await fetch(`${API}/services/stop/${svc.id}`, { method: "POST" });
      }
    }
  };

  const allRunning = SERVICES.every(s => statuses[s.id]);

  return (
    <div className="services-page">
      <div className="services-header-row">
        <div>
          <h2 className="services-title">Service Manager</h2>
          <p className="services-sub">Start, stop and monitor all backend processes from one place</p>
        </div>
        <div className="services-bulk-btns">
          <button className="bulk-btn start" onClick={startAll} disabled={allRunning}>
            ▶ Start All
          </button>
          <button className="bulk-btn stop" onClick={stopAll} disabled={!allRunning}>
            ■ Stop All
          </button>
        </div>
      </div>

      <div className="services-grid">
        {SERVICES.map((svc) => {
          const running = statuses[svc.id];
          const busy = loading[svc.id];
          const svcLogs = logs[svc.id] || [];
          return (
            <div key={svc.id} className={`svc-card ${running ? "running" : "stopped"}`}
              style={{ "--svc-color": svc.color }}>
              <div className="svc-card-top">
                <div className="svc-icon" style={{ color: svc.color }}>{svc.icon}</div>
                <div className="svc-info">
                  <div className="svc-name">{svc.label}</div>
                  <div className="svc-desc">{svc.desc}</div>
                </div>
                <div className="svc-right">
                  <div className={`svc-status-dot ${running ? "on" : "off"}`} />
                  <span className={`svc-status-label ${running ? "on" : "off"}`}>
                    {running ? "RUNNING" : "STOPPED"}
                  </span>
                  <button
                    className={`svc-toggle-btn ${running ? "stop-btn" : "start-btn"}`}
                    onClick={() => toggle(svc)}
                    disabled={busy}
                  >
                    {busy ? <span className="btn-spinner" /> : running ? "■ Stop" : "▶ Start"}
                  </button>
                </div>
              </div>
              <div className="svc-log-box" ref={el => logRefs.current[svc.id] = el}>
                {svcLogs.length === 0 ? (
                  <span className="log-empty">No output yet…</span>
                ) : (
                  svcLogs.map((line, i) => (
                    <div key={i} className={`log-line ${
                      line.toLowerCase().includes("error") ? "log-err" :
                      line.toLowerCase().includes("warn")  ? "log-warn" :
                      line.toLowerCase().includes("start") || line.toLowerCase().includes("running") ? "log-ok" : ""
                    }`}>{line}</div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="services-note panel">
        <div className="panel-header">
          <span className="panel-title">Backend Setup Notes</span>
          <span className="panel-badge">README</span>
        </div>
        <div className="setup-notes">
          <p>To enable service control, your FastAPI backend needs these endpoints:</p>
          <ul>
            <li><code>POST /api/services/start/&#123;service_id&#125;</code> — spawn subprocess</li>
            <li><code>POST /api/services/stop/&#123;service_id&#125;</code> — terminate process</li>
            <li><code>GET /api/services/status</code> — returns <code>&#123;"kafka": bool, "pipeline": bool&#125;</code></li>
            <li><code>GET /api/services/logs/&#123;service_id&#125;?lines=40</code> — returns <code>&#123;"lines": [...]&#125;</code></li>
          </ul>
          <p style={{marginTop:"8px", color:"var(--text-dim)"}}>
            Until those endpoints exist the toggle buttons will have no effect — all dashboard data polling continues regardless.
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── Sidebar Nav ──────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: "dashboard", icon: "⊞", label: "Dashboard",       sub: "Full overview" },
  { id: "services",  icon: "⚙", label: "Services",        sub: "Start / Stop" },
  { id: "map",       icon: "◈", label: "Live Map",         sub: "Congestion" },
  { id: "clusters",  icon: "⬡", label: "Clusters",         sub: "ST-DBSCAN" },
  { id: "alerts",    icon: "⚠", label: "Alert Feed",       sub: "Anomalies" },
  { id: "regime",    icon: "▦", label: "Regime Chart",     sub: "Markov" },
  { id: "drift",     icon: "◎", label: "Drift Detection",  sub: "Jaccard" },
  { id: "evolution", icon: "↯", label: "Evolution Log",    sub: "Lifecycle" },
];

export default function App() {
  const { data: stats }     = usePoll("/stats",     {});
  const { data: summary }   = usePoll("/summary",   []);
  const { data: alerts }    = usePoll("/alerts",    []);
  const { data: evolution } = usePoll("/evolution", []);
  const { data: drift }     = usePoll("/drift",     {});
  const [tick, setTick]     = useState(0);
  const [activeView, setActiveView] = useState("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), REFRESH_MS);
    return () => clearInterval(id);
  }, []);

  const isLive = stats.last_updated && (Date.now() / 1000 - stats.last_updated) < 15;

  const renderView = () => {
    switch (activeView) {
      case "services":  return <ServicesPanel />;
      case "map":       return <div className="single-view"><MapPanel tick={tick} /></div>;
      case "clusters":  return <div className="single-view"><ClusterTable summary={summary} /></div>;
      case "alerts":    return <div className="single-view"><AlertFeed alerts={alerts} /></div>;
      case "regime":    return <div className="single-view"><RegimeChart summary={summary} /></div>;
      case "drift":     return <div className="single-view"><DriftPanel drift={drift} /></div>;
      case "evolution": return <div className="single-view"><EvolutionLog evolution={evolution} /></div>;
      default:
        return (
          <>
            <StatsBar stats={stats} summary={summary} />
            <main className="main-grid">
              <div className="col-left">
                <MapPanel tick={tick} />
                <ClusterTable summary={summary} />
              </div>
              <div className="col-right">
                <AlertFeed alerts={alerts} />
                <RegimeChart summary={summary} />
                <DriftPanel drift={drift} />
                <EvolutionLog evolution={evolution} />
              </div>
            </main>
          </>
        );
    }
  };

  return (
    <div className={`shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-hex">⬡</span>
          {!sidebarCollapsed && <span className="logo-text">STRIX</span>}
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activeView === item.id ? "active" : ""}`}
              onClick={() => setActiveView(item.id)}
              title={sidebarCollapsed ? item.label : ""}
            >
              <span className="nav-icon">{item.icon}</span>
              {!sidebarCollapsed && (
                <span className="nav-labels">
                  <span className="nav-label">{item.label}</span>
                  <span className="nav-sub">{item.sub}</span>
                </span>
              )}
              {!sidebarCollapsed && activeView === item.id && (
                <span className="nav-active-bar" />
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          {!sidebarCollapsed && (
            <div className={`sidebar-live ${isLive ? "live" : "offline"}`}>
              <span className="pulse-dot" />
              {isLive ? "LIVE" : "OFFLINE"}
            </div>
          )}
          <button
            className="collapse-btn"
            onClick={() => setSidebarCollapsed(c => !c)}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? "»" : "«"}
          </button>
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <h1 className="title">
              {NAV_ITEMS.find(n => n.id === activeView)?.label || "TRAFFIC INTELLIGENCE"}
            </h1>
            <p className="subtitle">STRIX · Spatio-Temporal Mining Platform · Coimbatore, TN</p>
          </div>
            <div className="topbar-right">
            <div className={`live-badge ${isLive ? "live" : "offline"}`}>
              <span className="pulse-dot" />
              {isLive ? "LIVE" : "OFFLINE"}
            </div>
          </div>
        </header>

        <div className="view-area">
          {renderView()}
        </div>

        <footer className="footer">
          STRIX · Spatio-Temporal Mining Platform · ST-DBSCAN + Kafka + DTW · Ref: Shekhar et al. 2015
        </footer>
      </div>
    </div>
  );
}