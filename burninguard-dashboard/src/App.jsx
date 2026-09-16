import { useState } from 'react'
import spaceBackground from './assets/space-background.png'
import './App.css'
import AnomalyChart from './components/AnomalyChart'
import RiskHeatmap from './components/RiskHeatmap'
import AnomalyAnalysis from './pages/AnomalyAnalysis'
import DigitalTwin from './pages/DigitalTwin'
import Explainability from './pages/Explainability'
import AuditLog from './pages/AuditLog'

const anomalyData = [
  {
    dutId: "DUT-0042",
  lotId: "LOT-A17",
  checkpoint: "96h",
  score: "0.87",
  risk: "HIGH",
  status: "Anomaly",
  temperature: "85.4 °C",
  vcc: "3.31 V",
  iddq: "42.8 μA",
  leakage: "8.6 μA",
  delay: "12.4 ns",
  },
  {
    dutId: "DUT-0091",
  lotId: "LOT-B03",
  checkpoint: "120h",
  score: "0.94",
  risk: "CRITICAL",
  status: "Anomaly",
  temperature: "91.2 °C",
  vcc: "3.28 V",
  iddq: "58.3 μA",
  leakage: "11.7 μA",
  delay: "14.8 ns",
  },
  {
    dutId: "DUT-0137",
  lotId: "LOT-A17",
  checkpoint: "72h",
  score: "0.71",
  risk: "MEDIUM",
  status: "Anomaly",
  temperature: "79.6 °C",
  vcc: "3.30 V",
  iddq: "35.1 μA",
  leakage: "6.4 μA",
  delay: "11.6 ns",
  },
  {
    dutId: "DUT-0188",
  lotId: "LOT-C05",
  checkpoint: "144h",
  score: "0.82",
  risk: "HIGH",
  status: "Anomaly",
  temperature: "87.9 °C",
  vcc: "3.29 V",
  iddq: "47.6 μA",
  leakage: "9.8 μA",
  delay: "13.5 ns",
  },
];

function App() {
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [currentPage, setCurrentPage] = useState("dashboard")
  const [selectedQueueItem, setSelectedQueueItem] = useState(null);
  const [investigationQueue, setInvestigationQueue] = useState([
  {
    dutId: "DUT-0091",
    lotId: "LOT-B03",
    risk: "CRITICAL",
    score: "0.94",
    flaggedAt: "11 Sep 2026, 09:42",
    status: "Pending",
  },
  {
    dutId: "DUT-0042",
    lotId: "LOT-A17",
    risk: "HIGH",
    score: "0.87",
    flaggedAt: "11 Sep 2026, 09:18",
    status: "Under Investigation",
  },
]);
const markForInvestigation = () => {
  if (!selectedAnomaly) return;

  const alreadyInQueue = investigationQueue.some(
    (item) => item.dutId === selectedAnomaly.dutId
  );

  if (alreadyInQueue) {
    setInvestigationQueue((currentQueue) =>
      currentQueue.map((item) =>
        item.dutId === selectedAnomaly.dutId
          ? { ...item, status: "Under Investigation" }
          : item
      )
    );
  } else {
    setInvestigationQueue((currentQueue) => [
      ...currentQueue,
      {
        dutId: selectedAnomaly.dutId,
        lotId: selectedAnomaly.lotId,
        risk: selectedAnomaly.risk,
        score: selectedAnomaly.score,
        flaggedAt: new Date().toLocaleString(),
        status: "Under Investigation",
      },
    ]);
  }

  setSelectedAnomaly(null);
};
const markAsResolved = () => {
  if (!selectedQueueItem) return;

  setInvestigationQueue((currentQueue) =>
    currentQueue.map((item) =>
      item.dutId === selectedQueueItem.dutId
        ? { ...item, status: "Resolved" }
        : item
    )
  );

  setSelectedQueueItem(null);
  setSelectedAnomaly(null);
};
  return (
    <div
  className="dashboard"
  style={{
  backgroundImage: `url(${spaceBackground})`,
}}
>
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">BG</div>
          <div>
            <h2>BurnInGuard</h2>
            <span>AI 2.0</span>
          </div>
        </div>

        <nav>
  <a
    href="#"
    className={currentPage === "dashboard" ? "active" : ""}
    onClick={(event) => {
      event.preventDefault()
      setCurrentPage("dashboard")
    }}
  >
    Dashboard
  </a>

  <a
    href="#"
    className={currentPage === "anomaly-analysis" ? "active" : ""}
    onClick={(event) => {
      event.preventDefault()
      setCurrentPage("anomaly-analysis")
    }}
  >
    Anomaly Analysis
  </a>



<a
  href="#"
  className={currentPage === "digital-twin" ? "active" : ""}
  onClick={(event) => {
    event.preventDefault()
    setCurrentPage("digital-twin")
  }}
>
  Digital Twin
</a>

<a
  href="#"
  className={currentPage === "explainability" ? "active" : ""}
  onClick={(event) => {
    event.preventDefault()
    setCurrentPage("explainability")
  }}
>
  Explainability
</a>
  <a
  href="#"
  className={currentPage === "audit-log" ? "active" : ""}
  onClick={(event) => {
    event.preventDefault()
    setCurrentPage("audit-log")
  }}
>
  Audit Log
</a>
</nav>

        <div className="sidebar-footer">
          <span>QA ENGINEER</span>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
  {currentPage === "anomaly-analysis" ? (
    <AnomalyAnalysis />
  ) : currentPage === "digital-twin" ? (
    <DigitalTwin />
  ) : currentPage === "audit-log" ? (
    <AuditLog />
  ) : currentPage === "explainability" ? (
    <Explainability />
  ) : (
    <>
        <header className="topbar">
          <div>
            <p className="eyebrow">ISRO COMPONENT SCREENING</p>
            <h1>QA Dashboard</h1>
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            System Online
          </div>
        </header>

        {/* KPI Cards */}
        <section className="stats-grid">
          <div className="stat-card">
            <span>Components Tested</span>
            <strong>1,248</strong>
          </div>

          <div className="stat-card">
            <span>Anomalies Detected</span>
            <strong>87</strong>
          </div>

          <div className="stat-card">
            <span>High-Risk Components</span>
            <strong>23</strong>
          </div>

          <div className="stat-card">
            <span>Anomaly Rate</span>
            <strong>6.97%</strong>
          </div>
        </section>

        {/* Dashboard Content */}
        <section className="dashboard-grid">
          <div className="panel large-panel">
            <div className="panel-header">
              <div>
                <span className="panel-label">ANOMALY MONITORING</span>
                <h2>Anomaly Trend</h2>
              </div>
            </div>

            <div className="chart-placeholder">
              <AnomalyChart />
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-label">RISK ANALYSIS</span>
                <h2>Component Risk</h2>
              </div>
            </div>

            <div className="risk-placeholder">
               <RiskHeatmap />
            </div>
          </div>
        </section>

        {/* Recent Anomalies */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-label">QA INVESTIGATION</span>
              <h2>Recent Anomalies</h2>
            </div>

            <button
  className="view-all-button"
  onClick={() => setCurrentPage("anomaly-analysis")}
>
  View All
</button>
          </div>

          <div className="anomaly-table-wrapper">
  <table className="anomaly-table">
    <thead>
      <tr>
        <th>DUT ID</th>
        <th>LOT ID</th>
        <th>CHECKPOINT</th>
        <th>ANOMALY SCORE</th>
        <th>RISK</th>
        <th>STATUS</th>
        <th>ACTION</th>
      </tr>
    </thead>

    <tbody>
      {anomalyData.map((anomaly) => (
        <tr key={anomaly.dutId}>
          <td>{anomaly.dutId}</td>
          <td>{anomaly.lotId}</td>
          <td>{anomaly.checkpoint}</td>
          <td>{anomaly.score}</td>
          <td>
            <span className={`risk-badge ${anomaly.risk.toLowerCase()}`}>
              {anomaly.risk}
            </span>
          </td>
          <td>
            <span className="status-badge">
              {anomaly.status}
            </span>
          </td>
          <td>
            <button 
            className="view-button"
            onClick={() => setSelectedAnomaly(anomaly)}
            >
              View
            </button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
        </section>
              <section className="panel investigation-queue-panel">
        <div className="panel-header">
          <div>
            <span className="panel-label">QA WORKFLOW</span>
            <h2>Investigation Queue</h2>
          </div>

          <div className="queue-count">
            {investigationQueue.length} Active
          </div>
        </div>

        <div className="queue-table-wrapper">
          <table className="queue-table">
            <thead>
              <tr>
                <th>DUT ID</th>
                <th>LOT ID</th>
                <th>RISK</th>
                <th>ANOMALY SCORE</th>
                <th>FLAGGED AT</th>
                <th>STATUS</th>
                <th>ACTION</th>
              </tr>
            </thead>

            <tbody>
              {investigationQueue.map((item) => (
                <tr key={item.dutId}>
                  <td>{item.dutId}</td>
                  <td>{item.lotId}</td>

                  <td>
                    <span className={`risk-badge ${item.risk.toLowerCase()}`}>
                      {item.risk}
                    </span>
                  </td>

                  <td>{item.score}</td>
                  <td>{item.flaggedAt}</td>

                  <td>
                    <span className="queue-status">
                      {item.status}
                    </span>
                  </td>

                  <td>
                    <button
  className="review-button"
  onClick={() => {
    setSelectedQueueItem(item);

    const anomaly = anomalyData.find(
      (anomaly) => anomaly.dutId === item.dutId
    );

    setSelectedAnomaly(anomaly);
  }}
>
  Review
</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      ) : (
      </>
      )}
      </main>
      {selectedAnomaly && (
  <div
    className="modal-overlay"
    onClick={() => setSelectedAnomaly(null)}
  >
    <div
      className="investigation-modal"
      onClick={(event) => event.stopPropagation()}
    >
      <div className="modal-header">
        <div>
          <span className="panel-label">COMPONENT INVESTIGATION</span>
          <h2>{selectedAnomaly.dutId}</h2>
          <p>Lot: {selectedAnomaly.lotId}</p>
        </div>

        <button
          className="close-button"
          onClick={() => setSelectedAnomaly(null)}
        >
          ×
        </button>
      </div>

      <div className="investigation-status">
        <div>
          <span>RISK LEVEL</span>
          <strong>{selectedAnomaly.risk}</strong>
        </div>

        <div>
          <span>ANOMALY SCORE</span>
          <strong>{selectedAnomaly.score}</strong>
        </div>

        <div>
          <span>CHECKPOINT</span>
          <strong>{selectedAnomaly.checkpoint}</strong>
        </div>
      </div>

      <div className="telemetry-section">
        <span className="panel-label">TELEMETRY</span>

        <div className="telemetry-grid">
          <div>
            <span>Temperature</span>
            <strong>{selectedAnomaly.temperature}</strong>
          </div>

          <div>
            <span>VCC</span>
            <strong>{selectedAnomaly.vcc}</strong>
          </div>

          <div>
            <span>IDDQ</span>
            <strong>{selectedAnomaly.iddq}</strong>
          </div>

          <div>
            <span>Leakage</span>
            <strong>{selectedAnomaly.leakage}</strong>
          </div>

          <div>
            <span>Delay</span>
            <strong>{selectedAnomaly.delay}</strong>
          </div>
        </div>
      </div>

      <div className="explanation-section">
        <span className="panel-label">AI EXPLANATION</span>

        <p>
          The component was flagged because its observed telemetry
          deviates from the expected burn-in behavior.
        </p>
      </div>

      <div className="action-section">
  <span className="panel-label">INVESTIGATION STATUS</span>

  {selectedQueueItem ? (
    <>
      <div className="queue-review-status">
        <span>Current Status</span>
        <strong>{selectedQueueItem.status}</strong>
      </div>

      {selectedQueueItem.status !== "Resolved" && (
        <button className="investigation-button"
        onClick={markAsResolved}>
          Mark as Resolved
        </button>
      )}
    </>
  ) : (
    <button
      className="investigation-button"
      onClick={markForInvestigation}
    >
      Mark for Investigation
    </button>
  )}
</div>
    </div>
  </div>
)}
    </div>
  )
}

export default App
