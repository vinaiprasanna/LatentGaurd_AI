import { useState, useEffect, useCallback } from 'react'
import spaceBackground from './assets/space-background.png'
import './App.css'
import AnomalyChart from './components/AnomalyChart'
import RiskHeatmap from './components/RiskHeatmap'
import { api } from './api'
import AnomalyAnalysis from './pages/AnomalyAnalysis'
import DigitalTwin from './pages/DigitalTwin'
import Explainability from './pages/Explainability'
import AuditLog from './pages/AuditLog'
import CosmoAssistant from './components/CosmoAssistant'

function App() {
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [currentPage, setCurrentPage] = useState("dashboard")
  const [selectedQueueItem, setSelectedQueueItem] = useState(null)
  const [investigationQueue, setInvestigationQueue] = useState([])
  const [anomalyData, setAnomalyData] = useState([])
  const [stats, setStats] = useState({
    total_components: 0,
    anomalies_detected: 0,
    high_risk_components: 0,
    anomaly_rate: '0%',
  })
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  const syncInvestigationQueue = useCallback((duts) => {
    const flaggedDuts = duts.filter((dut) =>
      dut.data_quality_abnormal || dut.predicted_outcome === 'FAIL' || ['HIGH', 'CRITICAL'].includes(dut.risk_band)
    )
    setInvestigationQueue((currentQueue) => flaggedDuts.map((dut) => {
      const existing = currentQueue.find((item) => item.dutId === dut.dut_id)
      return {
        dutId: dut.dut_id,
        lotId: dut.lot_id,
        risk: dut.risk_band || 'LOW',
        score: Number(dut.anomaly_score ?? dut.anomaly_ensemble_score ?? dut.risk_score ?? 0).toFixed(2),
        flaggedAt: existing?.flaggedAt || new Date().toLocaleString(),
        status: existing?.status || 'Under Investigation',
        qualityFlags: dut.data_quality_flags || '',
      }
    }))
  }, [])

  const fetchDashboardData = useCallback(async () => {
    try {
      const [dutsData, statsData] = await Promise.all([
        api.getDuts(),
        api.getDashboardStats(),
      ])
      const duts = dutsData.duts || []
      setAnomalyData(duts)
      syncInvestigationQueue(duts)
      setStats(statsData)
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }, [syncInvestigationQueue])

  const handleCsvUpload = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setUploading(true)
    setUploadError('')
    try {
      const results = await api.predictCsv(file)
      setAnomalyData(results)
      syncInvestigationQueue(results)
      const total = results.length
      const highRisk = results.filter((item) => ['HIGH', 'CRITICAL'].includes(item.risk_band)).length
      const failures = results.filter((item) => item.predicted_outcome === 'FAIL').length
      setStats({
        total_components: total,
        anomalies_detected: highRisk,
        high_risk_components: highRisk,
        anomaly_rate: total ? `${((highRisk / total) * 100).toFixed(2)}%` : '0%',
        pass_rate: total ? `${(((total - failures) / total) * 100).toFixed(2)}%` : '0%',
      })
      setCurrentPage('dashboard')
    } catch (err) {
      setUploadError(err.message || 'CSV prediction failed')
    } finally {
      setUploading(false)
    }
  }

  useEffect(() => {
    const initialLoad = setTimeout(fetchDashboardData, 0)
    const interval = setInterval(fetchDashboardData, 30000)
    return () => {
      clearTimeout(initialLoad)
      clearInterval(interval)
    }
  }, [fetchDashboardData])

  const markForInvestigation = () => {
    if (!selectedAnomaly) return
    const alreadyInQueue = investigationQueue.some(
      (item) => item.dutId === selectedAnomaly.dutId
    )
    if (alreadyInQueue) {
      setInvestigationQueue((currentQueue) =>
        currentQueue.map((item) =>
          item.dutId === selectedAnomaly.dutId
            ? { ...item, status: "Under Investigation" }
            : item
        )
      )
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
      ])
    }
    setSelectedAnomaly(null)
  }

  const markAsResolved = () => {
    if (!selectedQueueItem) return
    setInvestigationQueue((currentQueue) =>
      currentQueue.map((item) =>
        item.dutId === selectedQueueItem.dutId
          ? { ...item, status: "Resolved" }
          : item
      )
    )
    setSelectedQueueItem(null)
    setSelectedAnomaly(null)
  }

  const anomalyDataWithRisk = anomalyData.map((d) => ({
    dutId: d.dut_id,
    lotId: d.lot_id,
    checkpoint: `${d.checkpoint_h || 168}h`,
    score: (d.anomaly_score ?? d.anomaly_ensemble_score)
      ? (typeof (d.anomaly_score ?? d.anomaly_ensemble_score) === 'number'
        ? (d.anomaly_score ?? d.anomaly_ensemble_score).toFixed(2)
        : (d.anomaly_score ?? d.anomaly_ensemble_score))
      : '0.00',
    risk: d.risk_band || 'LOW',
    status: d.predicted_outcome === 'FAIL' ? 'Anomaly' : 'Normal',
    temperature: d.temperature_c ? `${d.temperature_c} °C` : '--',
    vcc: d.vcc_v ? `${d.vcc_v} V` : '--',
    iddq: d.iddq_uA ? `${d.iddq_uA} μA` : '--',
    leakage: d.leakage_uA ? `${d.leakage_uA} μA` : '--',
    delay: d.delay_ns ? `${d.delay_ns} ns` : '--',
    explanation: d.explanation || 'No explanation available',
    qualityFlags: d.data_quality_flags || '',
  }))

  return (
    <div className="dashboard" style={{ backgroundImage: `url(${spaceBackground})` }}>
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">BG</div>
          <div>
            <h2>BurnInGuard</h2>
            <span>AI 2.0</span>
          </div>
        </div>
        <nav>
          <a href="#" className={currentPage === "dashboard" ? "active" : ""} onClick={(e) => { e.preventDefault(); setCurrentPage("dashboard") }}>Dashboard</a>
          <a href="#" className={currentPage === "anomaly-analysis" ? "active" : ""} onClick={(e) => { e.preventDefault(); setCurrentPage("anomaly-analysis") }}>Anomaly Analysis</a>
          <a href="#" className={currentPage === "digital-twin" ? "active" : ""} onClick={(e) => { e.preventDefault(); setCurrentPage("digital-twin") }}>Digital Twin</a>
          <a href="#" className={currentPage === "explainability" ? "active" : ""} onClick={(e) => { e.preventDefault(); setCurrentPage("explainability") }}>Explainability</a>
          <a href="#" className={currentPage === "audit-log" ? "active" : ""} onClick={(e) => { e.preventDefault(); setCurrentPage("audit-log") }}>Audit Log</a>
        </nav>
        <div className="sidebar-footer">
          <input id="csv-upload" type="file" accept=".csv,text/csv" onChange={handleCsvUpload} hidden />
          <label className="csv-upload-button" htmlFor="csv-upload">
            <span>{uploading ? 'PROCESSING CSV...' : 'IMPORT INPUT CSV'}</span>
          </label>
          {uploadError && <p className="upload-error" role="alert">{uploadError}</p>}
          <span>QA ENGINEER</span>
        </div>
      </aside>
      <main className="main-content">
        {currentPage === "anomaly-analysis" ? (
          <AnomalyAnalysis anomalyData={anomalyData} />
        ) : currentPage === "digital-twin" ? (
          <DigitalTwin anomalyData={anomalyData} />
        ) : currentPage === "audit-log" ? (
          <AuditLog />
        ) : currentPage === "explainability" ? (
          <Explainability anomalyData={anomalyData} />
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
            {loading ? (
              <div className="stats-grid">
                {[1,2,3,4].map(i => <div key={i} className="stat-card"><span>Loading...</span><strong>--</strong></div>)}
              </div>
            ) : (
              <>
                <section className="stats-grid">
                  <div className="stat-card">
                    <span>Components Tested</span>
                    <strong>{stats.total_components || 0}</strong>
                  </div>
                  <div className="stat-card">
                    <span>Anomalies Detected</span>
                    <strong>{stats.anomalies_detected || 0}</strong>
                  </div>
                  <div className="stat-card">
                    <span>High-Risk Components</span>
                    <strong>{stats.high_risk_components || 0}</strong>
                  </div>
                  <div className="stat-card">
                    <span>Anomaly Rate</span>
                    <strong>{stats.anomaly_rate || '0%'}</strong>
                  </div>
                </section>
                <section className="dashboard-grid">
                  <div className="panel large-panel">
                    <div className="panel-header">
                      <div>
                        <span className="panel-label">ANOMALY MONITORING</span>
                        <h2>Anomaly Trend</h2>
                      </div>
                    </div>
                    <div className="chart-placeholder">
                      <AnomalyChart anomalyData={anomalyData} />
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
                      <RiskHeatmap anomalyData={anomalyData} />
                    </div>
                  </div>
                </section>
                <section className="panel">
                  <div className="panel-header">
                    <div>
                      <span className="panel-label">QA INVESTIGATION</span>
                      <h2>Recent Anomalies</h2>
                    </div>
                    <button className="view-all-button" onClick={() => setCurrentPage("anomaly-analysis")}>View All</button>
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
                        {anomalyDataWithRisk.slice(0, 5).map((anomaly) => (
                          <tr key={anomaly.dutId}>
                            <td>{anomaly.dutId}</td>
                            <td>{anomaly.lotId}</td>
                            <td>{anomaly.checkpoint}</td>
                            <td>{anomaly.score}</td>
                            <td><span className={`risk-badge ${anomaly.risk.toLowerCase()}`}>{anomaly.risk}</span></td>
                            <td><span className="status-badge">{anomaly.status}</span></td>
                            <td><button className="view-button" onClick={() => { setSelectedQueueItem(null); setSelectedAnomaly(anomaly); }}>View</button></td>
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
                    <div className="queue-count">{investigationQueue.length} Active</div>
                  </div>
                  <div className="queue-table-wrapper">
                    <table className="queue-table">
                      <thead>
                        <tr><th>DUT ID</th><th>LOT ID</th><th>RISK</th><th>ANOMALY SCORE</th><th>FLAGGED AT</th><th>STATUS</th><th>REASON</th><th>ACTION</th></tr>
                      </thead>
                      <tbody>
                        {investigationQueue.map((item) => (
                          <tr key={item.dutId}>
                            <td>{item.dutId}</td><td>{item.lotId}</td>
                            <td><span className={`risk-badge ${item.risk.toLowerCase()}`}>{item.risk}</span></td>
                            <td>{item.score}</td><td>{item.flaggedAt}</td>
                            <td><span className="queue-status">{item.status}</span></td>
                            <td>{item.qualityFlags || 'Model risk flag'}</td>
                            <td><button className="review-button" onClick={() => { setSelectedQueueItem(item); const anomaly = anomalyDataWithRisk.find(a => a.dutId === item.dutId); setSelectedAnomaly(anomaly); }}>Review</button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </>
            )}
          </>
        )}
        {selectedAnomaly && (
          <div className="modal-overlay" onClick={() => setSelectedAnomaly(null)}>
            <div className="investigation-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <span className="panel-label">COMPONENT INVESTIGATION</span>
                  <h2>{selectedAnomaly.dutId}</h2>
                  <p>Lot: {selectedAnomaly.lotId}</p>
                </div>
                <button className="close-button" onClick={() => setSelectedAnomaly(null)}>×</button>
              </div>
              <div className="investigation-status">
                <div><span>RISK LEVEL</span><strong>{selectedAnomaly.risk}</strong></div>
                <div><span>ANOMALY SCORE</span><strong>{selectedAnomaly.score}</strong></div>
                <div><span>CHECKPOINT</span><strong>{selectedAnomaly.checkpoint}</strong></div>
              </div>
              <div className="telemetry-section">
                <span className="panel-label">TELEMETRY</span>
                <div className="telemetry-grid">
                  <div><span>Temperature</span><strong>{selectedAnomaly.temperature}</strong></div>
                  <div><span>VCC</span><strong>{selectedAnomaly.vcc}</strong></div>
                  <div><span>IDDQ</span><strong>{selectedAnomaly.iddq}</strong></div>
                  <div><span>Leakage</span><strong>{selectedAnomaly.leakage}</strong></div>
                  <div><span>Delay</span><strong>{selectedAnomaly.delay}</strong></div>
                </div>
              </div>
              <div className="explanation-section">
                <span className="panel-label">AI EXPLANATION</span>
                <p>{selectedAnomaly.explanation}</p>
              </div>
              <div className="action-section">
                <span className="panel-label">INVESTIGATION STATUS</span>
                {selectedQueueItem ? (
                  <>
                    <div className="queue-review-status"><span>Current Status</span><strong>{selectedQueueItem.status}</strong></div>
                    {selectedQueueItem.status !== "Resolved" && <button className="investigation-button" onClick={markAsResolved}>Mark as Resolved</button>}
                  </>
                ) : (
                  <button className="investigation-button" onClick={markForInvestigation}>Mark for Investigation</button>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
      <CosmoAssistant anomalyData={anomalyData} />
    </div>
  )
}

export default App
