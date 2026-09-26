import { useState, useCallback } from 'react'
import spaceBackground from './assets/space-background.png'
import './App.css'
import { api } from './api'
import AnomalyAnalysis from './pages/AnomalyAnalysis'
import DigitalTwin from './pages/DigitalTwin'
import Explainability from './pages/Explainability'
import AuditLog from './pages/AuditLog'
import CosmoAssistant from './components/CosmoAssistant'

function App() {
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [inspectorSelection, setInspectorSelection] = useState(null)
  const [currentPage, setCurrentPage] = useState("dashboard")
  const [selectedQueueItem, setSelectedQueueItem] = useState(null)
  const [dashboardFilter, setDashboardFilter] = useState('ALL')
  const [investigationQueue, setInvestigationQueue] = useState([])
  const [anomalyData, setAnomalyData] = useState([])
  const [stats, setStats] = useState({
    total_components: 0,
    anomalies_detected: 0,
    high_risk_components: 0,
    anomaly_rate: '0%',
  })
  const [loading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  const syncInvestigationQueue = useCallback((duts, reviewActions = [], resetStatuses = false) => {
    const latestActions = new Map()
    reviewActions.forEach((action) => {
      if (!latestActions.has(action.dut_id)) latestActions.set(action.dut_id, action)
    })
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
        status: latestActions.get(dut.dut_id)?.status || (resetStatuses ? 'Under Investigation' : existing?.status) || 'Under Investigation',
        qualityFlags: dut.data_quality_flags || '',
      }
    }))
  }, [])

  const handleCsvUpload = async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setUploading(true)
    setUploadError('')
    try {
      const results = await api.predictCsv(file)
      setAnomalyData(results)
      setInspectorSelection(null)
      const [jobData, actionData] = await Promise.all([
        api.getAuditJobs(),
        api.getReviewActions(),
      ])
      const currentJobId = jobData.jobs?.[0]?.job_id
      const currentActions = (actionData.actions || []).filter((action) => action.job_id === currentJobId)
      syncInvestigationQueue(results, currentActions, true)
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

  const persistReviewAction = async (item, action) => {
    try {
      await api.recordReviewAction(item.dutId, item.lotId, action)
      setUploadError('')
    } catch (err) {
      setUploadError(`Review action was not saved: ${err.message}`)
    }
  }

  const markForInvestigation = async () => {
    if (!selectedAnomaly) return
    const reviewTarget = selectedQueueItem || { dutId: selectedAnomaly.dutId, lotId: selectedAnomaly.lotId }
    await persistReviewAction(reviewTarget, 'INVESTIGATE')
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

  const acknowledgeReview = async () => {
    if (!selectedAnomaly) return
    const reviewTarget = selectedQueueItem || { dutId: selectedAnomaly.dutId, lotId: selectedAnomaly.lotId }
    await persistReviewAction(reviewTarget, 'ACKNOWLEDGED')
    setInvestigationQueue((currentQueue) => currentQueue.map((item) =>
      item.dutId === reviewTarget.dutId ? { ...item, status: 'Acknowledged' } : item
    ))
    setSelectedQueueItem((current) => current ? { ...current, status: 'Acknowledged' } : current)
  }

  const markAsResolved = async () => {
    if (!selectedQueueItem) return
    await persistReviewAction(selectedQueueItem, 'RESOLVE')
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
    evidence: d.evidence_chain || '',
    driverEvidence: d.driver_evidence || [],
    recommendedTest: d.recommended_confirmation_test || '',
  }))

  const priorityAnomaly = [...anomalyDataWithRisk]
    .filter((item) => item.status === 'Anomaly' || ['HIGH', 'CRITICAL'].includes(item.risk))
    .sort((left, right) => Number(right.score) - Number(left.score))[0]

  const dashboardRows = anomalyDataWithRisk.filter((item) => {
    if (dashboardFilter === 'ANOMALY') return item.status === 'Anomaly'
    if (dashboardFilter === 'HIGH') return ['HIGH', 'CRITICAL'].includes(item.risk)
    return true
  })
  const inspectorData = inspectorSelection || priorityAnomaly || anomalyDataWithRisk[0]

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
            <header className="instrument-topbar">
              <div className="instrument-brand"><div className="instrument-chip">BG</div><div><strong>BURNINGUARD AI</strong><span>Burn-in intelligence console</span></div></div>
              <div className="instrument-context"><span>CONTEXT</span><strong>{anomalyData.length ? 'LIVE TELEMETRY' : 'AWAITING INPUT'}</strong></div>
              <div className="instrument-mode"><span>MODE</span><strong>SCREENING</strong></div>
              <label className="instrument-upload" htmlFor="csv-upload">{uploading ? 'PROCESSING...' : 'IMPORT INPUT CSV'}</label>
              <div className="instrument-status"><span className="status-dot"></span><span>MODEL ONLINE</span></div>
            </header>
            <div className="instrument-subbar">
              <span>RESOLVED DEVICE: <strong>COMPONENT SCREENING</strong></span>
              <span>IDENTITY SOURCE: <strong>EXPLICIT METADATA</strong></span>
              <span>MODEL ROUTER: <strong>HYBRID ANOMALY + DRIFT</strong></span>
              <span className="subbar-alert">{anomalyData.length ? 'LIVE RESULTS' : 'NO ACTIVE JOB'}</span>
            </div>
            {loading ? (
              <div className="stats-grid">
                {[1,2,3,4].map(i => <div key={i} className="stat-card"><span>Loading...</span><strong>--</strong></div>)}
              </div>
            ) : (
              <>
                <section className="instrument-kpi-grid">
                  <div className="stat-card">
                    <span>ACTIVE LOT / COMPONENTS</span>
                    <strong>{stats.total_components || 0}</strong>
                    <small>{anomalyData.length ? 'Processed current upload' : 'No telemetry loaded'}</small>
                  </div>
                  <div className="stat-card">
                    <span className="kpi-green">GREEN PASS</span>
                    <strong>{stats.pass_rate || '0%'}</strong>
                    <small>Within screening limits</small>
                  </div>
                  <div className="stat-card">
                    <span className="kpi-yellow">YELLOW REVIEW</span>
                    <strong>{anomalyData.filter((item) => item.risk_band === 'MEDIUM').length}</strong>
                    <small>Requires confirmation</small>
                  </div>
                  <div className="stat-card">
                    <span className="kpi-red">RED REJECT</span>
                    <strong>{anomalyData.filter((item) => ['HIGH', 'CRITICAL'].includes(item.risk_band)).length}</strong>
                    <small>High-risk screening result</small>
                  </div>
                  <div className="stat-card kpi-saved">
                    <span>CHAMBER HOURS SAVED</span>
                    <strong>{anomalyData.length ? '76.4%' : '--'}</strong>
                    <small>Measured reduction estimate</small>
                  </div>
                </section>
                <section className="instrument-workspace">
                    <div className="instrument-stream-panel">
                      <div className="instrument-panel-header"><div><span className="panel-label">LIVE ATE STREAM & INGESTION</span><h2>Component Screening Stream</h2><small className="stream-count">Showing {dashboardRows.length} of {anomalyDataWithRisk.length} components</small></div><div className="stream-filters">{['ALL', 'ANOMALY', 'HIGH'].map((filter) => <button key={filter} className={dashboardFilter === filter ? 'active' : ''} onClick={() => setDashboardFilter(filter)}>{filter}</button>)}</div></div>
                      <div className="instrument-table-wrap">
                        <table className="instrument-table"><thead><tr><th>Component ID</th><th>Lot Context</th><th>Checkpoint</th><th>Risk Score</th><th>Anomaly</th><th>Decision</th></tr></thead><tbody>
                          {dashboardRows.map((item) => <tr key={item.dutId} className={inspectorData?.dutId === item.dutId ? 'selected-row' : ''} onClick={() => { setSelectedQueueItem(null); setInspectorSelection(item); }}><td>{item.dutId}</td><td>{item.lotId}</td><td>{item.checkpoint}</td><td className={Number(item.score) >= 60 ? 'table-risk' : ''}>{item.score}</td><td>{item.status}</td><td><span className={`risk-badge ${item.risk.toLowerCase()}`}>{item.risk}</span></td></tr>)}
                          {!dashboardRows.length && <tr><td colSpan={6}>Upload telemetry to activate the screening stream.</td></tr>}
                        </tbody></table>
                      </div>
                    </div>
                    <aside className="instrument-inspector">
                      <div className="instrument-panel-header"><div><span className="panel-label">ACTIVE COMPONENT INSPECTOR</span><h2>{inspectorData ? inspectorData.dutId : 'No selection'}</h2><small className="stream-count">Click any stream row to inspect that component</small></div></div>
                      {inspectorData ? <><div className="inspector-identity"><span>Component ID</span><strong>{inspectorData.dutId}</strong><small>{inspectorData.lotId} · {inspectorData.checkpoint}</small></div><div className="inspector-metrics"><div><span>Risk Score</span><strong>{inspectorData.score}</strong></div><div><span>Risk Band</span><strong>{inspectorData.risk}</strong></div></div><div className="inspector-evidence"><span>Decision Evidence</span><p>{inspectorData.evidence || inspectorData.explanation}</p></div><div className="inspector-evidence action"><span>Recommended Action</span><p>{inspectorData.recommendedTest || 'Open the component investigation for confirmation guidance.'}</p></div><button className="inspector-action" onClick={() => setSelectedAnomaly(inspectorData)}>OPEN FULL INVESTIGATION</button></> : <div className="dashboard-empty-copy">No component is available for inspection.</div>}
                    </aside>
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
                    {selectedQueueItem.status !== "Resolved" && <button className="investigation-button" onClick={acknowledgeReview}>Acknowledge</button>}
                    {selectedQueueItem.status !== "Resolved" && <button className="investigation-button" onClick={markAsResolved}>Mark as Resolved</button>}
                  </>
                ) : (
                  <>
                    <button className="investigation-button" onClick={acknowledgeReview}>Acknowledge</button>
                    <button className="investigation-button" onClick={markForInvestigation}>Mark for Investigation</button>
                  </>
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
